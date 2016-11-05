# -*- coding: UTF-8 -*-

# COPYRIGHT (c) 2016 Cristóbal Ganter
#
# GNU AFFERO GENERAL PUBLIC LICENSE
#    Version 3, 19 November 2007
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Render the user panel and process all user messages.

This module patches the :class:`controller.MSGHandler`
class, adding the
:meth:`controller.MSGHandler.send_user_not_loaded_error`,
:meth:`controller.MSGHandler.send_room_not_loaded_error` and
:meth:`controller.MSGHandler.logout_and_close` methods.
"""

from functools import partialmethod

import jwt
from tornado.gen import coroutine
from pymongo.errors import OperationFailure

import src
from controller import MSGHandler
from backend_modules import router
from src import messages as msg
from src.db import User, Code, NoObjectReturnedFromDB, \
    ConditionNotMetError, Course, Room
from src.pub_sub import MalformedMessageError
from src.wsclass import subscribe

_path = msg.join_path('panels', 'user')

MSGHandler.send_user_not_loaded_error = partialmethod(
    MSGHandler.send_error,
    'userNotLoaded',
    description='There was no loaded user when '
                'this message arrived.'
)

MSGHandler.send_room_not_loaded_error = partialmethod(
    MSGHandler.send_error,
    'roomNotLoaded',
    description='There was no loaded room when '
    'this message arrived.'
)


def _logout_and_close(self, reason):
    """Send a logout message and close the connection."""
    self.write_message({'type': 'logout'})
    self.close(1000, reason)
    self.clean_closed = True
MSGHandler.logout_and_close = _logout_and_close


class UserPanel(src.boiler_ui_module.BoilerUIModule):
    id_ = 'user-panel'
    classes = {'scrolling-panel', 'system'}
    name = 'Usuario'
    conf = {
        'static_url_prefix': '/user/',
        'static_path': './panels/user/static',
        'css_files': ['user.css'],
        'js_files': ['user.js'],
    }

    def render(self):
        return self.render_string(
            '../panels/user/user.html')


class UserWSC(src.wsclass.WSClass):

    """Process user messages"""

    _path = msg.join_path(_path, 'UserWSC')

    @staticmethod
    def should_run_room_deassign_course(
            has_course, was_none, was_student, was_teacher,
            is_none, is_student, is_teacher, distinct_room):

        return was_teacher and has_course and (
            is_student or is_teacher and distinct_room)

    @staticmethod
    def should_run_user_deassign_course(
            has_course, was_none, was_student, was_teacher,
            is_none, is_student, is_teacher, distinct_room):

        student_condition = \
            was_student and (
                not is_student or distinct_room)

        teacher_condition = \
            was_teacher and not is_none and (
                not is_teacher or distinct_room)

        return has_course and (
            student_condition or
            teacher_condition
        )

    @staticmethod
    def should_run_use_seat(
            has_course, was_none, was_student, was_teacher,
            is_none, is_student, is_teacher, distinct_room):

        return is_student

    @staticmethod
    def should_run_logout_other_instances(
            has_course, was_none, was_student, was_teacher,
            is_none, is_student, is_teacher, distinct_room):

        return \
            was_student or \
            is_student or \
            was_none and not is_none or \
            is_teacher and distinct_room

    @staticmethod
    def should_run_load_course(
            has_course, was_none, was_student, was_teacher,
            is_none, is_student, is_teacher, distinct_room):

        return \
            has_course and not distinct_room and (
                was_student and is_student or
                was_teacher and is_teacher
            )

    @staticmethod
    def should_run_redirect_to_teacher_view(
            has_course, was_none, was_student, was_teacher,
            is_none, is_student, is_teacher, distinct_room):

        return was_teacher and is_none

    def __init__(self, handler):
        super().__init__(handler)
        self.session_start_ok = False
        self.block_logout = False
        self.user_state_at_exclusive_login = None
        self.dont_leave_seat = False

    @coroutine
    def load_user(self, token):
        try:
            uid = jwt.decode(token, verify=False)['id']
            user = yield User.get(uid)
            jwt.decode(token, user.secret)
            self.handler.user = user

        except NoObjectReturnedFromDB as norfdb:
            ite = jwt.InvalidTokenError(
                'No user was found in the database for '
                'this token.'
            )
            raise ite from norfdb

    @subscribe('message.filter.student', 'l')
    @coroutine
    def redirect_message_if_user_is_student(
            self, message, content=True):
        """Redirects a message if the user is a student.

        This coroutine redirects a message to the local
        channel only if the current user is a student.

        :param dict message:
            The message that should be redirected if the
            user is a student.

        :param bool content:
            If ``True``, just the object corresponding to
            the ``'content'`` key of ``message`` will be
            sent.
            If ``False``, the whole message will be sent.

        :raises MalformedMessageError:
            If ``content`` is ``True``, but ``message``
            doesn't have the ``'content'`` key.

        :raises NotDictError:
            If ``message`` is not a dictionary.

        :raises NoMessageTypeError:
            If the message or it's content doesn't have the
            ``'type'`` key.

        :raises NoActionForMsgTypeError:
            If ``send_function`` of the ``PubSub`` object
            wasn't specified during object creation and
            there's no registered action for this message
            type.

        :raises AttributeError:
            If the user is not yet loaded or if the user is
            ``None``.
        """
        try:
            if self.handler.user.status == 'seat':
                self.redirect_to('l', message, content)
        except:
            raise

    @subscribe('teacherMessage', 'l')
    @coroutine
    def redirect_message_if_user_is_teacher(
            self, message, content=True):
        """Redirects a message if the user is a teacher.

        This coroutine redirects a message to the local
        channel only if the current user is a teacher.

        :param dict message:
            The message that should be redirected if the
            user is a teacher.

        :param bool content:
            If ``True``, just the object corresponding to
            the ``'content'`` key of ``message`` will be
            sent.
            If ``False``, the whole message will be sent.

        :raises MalformedMessageError:
            If ``content`` is ``True``, but ``message``
            doesn't have the ``'content'`` key.

        :raises NotDictError:
            If ``message`` is not a dictionary.

        :raises NoMessageTypeError:
            If the message or it's content doesn't have the
            ``'type'`` key.

        :raises NoActionForMsgTypeError:
            If ``send_function`` of the ``PubSub`` object
            wasn't specified during object creation and
            there's no registered action for this message
            type.

        :raises AttributeError:
            If the user is not yet loaded or if the user is
            ``None``.
        """
        try:
            if self.handler.user.status == 'room':
                self.redirect_to('l', message, content)
        except:
            raise

    @subscribe('logout', 'l')
    def logout(self, message):
        try:
            if self.block_logout:
                self.block_logout = False
            else:
                self.user_state_at_exclusive_login = \
                    message.get(
                        'user_state_at_exclusive_login')

                self.dont_leave_seat = message.get(
                    'dont_leave_seat', False)

                self.handler.logout_and_close(
                    message['reason'])

        except KeyError as ke:
            if 'reason' not in message:
                mme = MalformedMessageError(
                    "'reason' key not found in message.")
                raise mme from ke
            else:
                raise

    @subscribe('userMessage', channels={'w', 'l'})
    def send_user_message(self, message):
        """Send a message to all instances of a single user.

        The user id is appended to the message type and
        ``message`` is sent through the database.

        .. todo::
            *   Change the message type of the subscription
                to be organised by namespace.
            *   Change this method so that it uses
                self.handler.user_msg_type.
        """
        try:
            message['type'] = '{}({})'.format(
                message['type'], self.handler.user.id)

            self.redirect_to('d', message)

        except MalformedMessageError:
            self.handler.send_malformed_message_error(
                message)
            msg.malformed_message(_path, message)

        except AttributeError:
            if not hasattr(self.handler, 'user'):
                self.handler.send_user_not_loaded_error(
                    message)
            else:
                raise

    @subscribe(
        'user.message.frontend.send', channels={'w', 'l'})
    def send_frontend_user_message(self, message):
        """Send a message to all clients of a single user.

        .. todo::
            *   Review the error handling and documentation
                of this funcion.
        """
        try:
            self.pub_subs['d'].send_message(
                {
                    'type': self.handler.user_msg_type,
                    'content': {
                        'type': 'toFrontend',
                        'content': message['content']
                    }
                }
            )

        except:
            raise

    def sub_to_user_messages(self):
        """Route messages of the same user to the local PS.

        This method subscribes
        :meth:`backend_modules.router.RouterWSC.to_local` to
        the messages of type ``userMessage(uid)`` coming
        from the database pub-sub. Where ``uid`` is the
        current user id.

        After the execution of this method,
        ``self.handler.user_msg_type`` contains the message
        type to be used to send messages to all instances of
        the user.
        """
        self.handler.user_msg_type = \
            'userMessage({})'.format(self.handler.user.id)

        router_object = self.handler.ws_objects[
            router.RouterWSC]
        self.register_action_in(
            self.handler.user_msg_type,
            action=router_object.to_local,
            channels={'d'}
        )

    def send_session_start_error(self, message, causes):
        """Send a session error message to the client.

        :param dict message:
            The message that caused the error.

        :param str causes:
            A string explaining the posible causes of the
            error.
        """
        try:
            self.handler.send_error(
                'session.start.error',
                message,
                'La sesión no se ha podido iniciar. ' +
                causes
            )

        except TypeError as e:
            if not isinstance(message, dict):
                te = TypeError(
                    'message should be a dictionary.')
                raise te from e

            elif not isinstance(causes, str):
                te = TypeError(
                    'causes should be a string.')
                raise te from e

            else:
                raise

    @coroutine
    def load_room_code(self, room_code_str):
        """Load the room code and room from the db.

        ..todo::
            * Write error handling.
        """
        if room_code_str == 'none':
            room_code = None
            room = None
            code_type = 'none'
            room_name = None
            seat_id = None
        else:
            room_code = yield Code.get(room_code_str)
            room = yield room_code.room
            code_type = room_code.code_type.value
            room_name = room.name
            seat_id = room_code.seat_id

        self.handler.room_code = room_code
        self.handler.room = room

        return (code_type, room_name, seat_id)

    def redirect_to_teacher_view(self, room_code, message):
        """Redirect the client to the current teacher view.

        .. todo:
            *   Use send_session_start_error instead of
                handler.send_error.
        """
        if room_code == 'none':
            err_msg = "Can't redirect user to the " \
                "teacher view. This can be caused by an " \
                "inconsistency in the database."

            self.handler.send_error(
                'databaseInconsistency', message, err_msg)

            raise Exception(err_msg)

        self.pub_subs['w'].send_message(
            {
                'type': 'replaceLocation',
                'url': room_code
            }
        )

    @subscribe('session.start', 'w')
    @coroutine
    def startSession(self, message):
        """Start a user session

        .. todo::
            *   Add a variable that indicates the last stage
                that was executed successfully. So that the
                finally clause can clean the mess properly.
        """
        try:
            yield self.load_user(message['token'])
            self.sub_to_user_messages()
            code_type, room_name, seat_id = \
                yield self.load_room_code(
                    message['room_code'])

            user = self.handler.user
            room_code = self.handler.room_code
            room = self.handler.room

            course_id = user.course_id
            has_course = course_id is not None

            was_none = (user.status == 'none')
            was_student = (user.status == 'seat')
            was_teacher = (user.status == 'room')

            is_none = (code_type == 'none')
            is_student = (code_type == 'seat')
            is_teacher = (code_type == 'room')

            distinct_room = not (
                room_name is None or
                user.room_name is None or
                room_name == user.room_name
            )

            same_seat = (seat_id == user.seat_id) and \
                not distinct_room

            transition_data = (
                has_course, was_none, was_student,
                was_teacher, is_none, is_student,
                is_teacher, distinct_room
            )

            # Redirect to Teacher View
            if self.should_run_redirect_to_teacher_view(
                    *transition_data):
                self.redirect_to_teacher_view(
                    user.room_code, message)
                # The rest of the code is not executed.
                return

            # Room Deassign Course
            '''This should always run before "User Deassign
            Course"'''
            if self.should_run_room_deassign_course(
                    *transition_data):
                if distinct_room:
                    r = yield Room.get(user.room_name)
                else:
                    r = room

                yield r.deassign_course(course_id)

            # User Deassign Course
            if self.should_run_user_deassign_course(
                    *transition_data):
                yield user.deassign_course()

            # Logout Other Instances
            if self.should_run_logout_other_instances(
                    *transition_data):
                self.block_logout = True
                self.pub_subs['d'].send_message(
                    {
                        'type': self.handler.user_msg_type,
                        'content': {
                            'type': 'logout',
                            'reason': 'exclusiveLogin',
                            'user_state_at_exclusive_login':
                                user._data,
                            'dont_leave_seat': same_seat,
                        }
                    }
                )

            # Use Seat
            if self.should_run_use_seat(*transition_data) \
                    and (not same_seat or
                         user.instances == 0):
                yield room.use_seat(room_code.seat_id)

            # Load Course
            if self.should_run_load_course(
                    *transition_data):
                self.handler.course = yield Course.get(
                    course_id)

            # Increase Instances
            yield self.handler.user.increase_instances()

            yield self.handler.user.store_dict(
                {
                    'status': code_type,
                    'room_code': message['room_code'],
                    'room_name': room_name,
                    'seat_id': seat_id,
                }
            )

        except jwt.InvalidTokenError:
            self.handler.logout_and_close('invalidToken')

        except ConditionNotMetError:
            self.send_session_start_error(
                message,
                'Es probable que este error se daba a que '
                'el asiento que desea registrar ya está '
                'usado.'
            )

        except OperationFailure:
            self.send_session_start_error(
                message,
                'Una operación de la base de datos ha '
                'fallado.'
            )

        except KeyError:
            keys_in_message = all(
                map(
                    lambda k: k in message,
                    ('token', 'room_code')
                )
            )
            if not keys_in_message:
                self.handler.send_malformed_message_error(
                    message)
            else:
                raise

        else:
            self.session_start_ok = True

            self.pub_subs['w'].send_message(
                {
                    'type': 'session.start.ok',
                    'code_type': code_type,
                    'course_id': user.course_id
                }
            )

        finally:
            if not self.session_start_ok:
                pass

    @subscribe('getUserName', 'w')
    def get_user_name(self, message):
        """Send the user's name to the client.

        .. todo::
            *   Re-raise attribute error
            *   review error handling.
        """
        try:
            name = self.handler.user.name
            self.pub_subs['w'].send_message(
                {'type': 'userName',
                 'name': name})
        except AttributeError:
            self.handler.send_user_not_loaded_error(message)

    @coroutine
    def end_room_usage(self, user, is_teacher, is_student):
        try:
            room_code = self.handler.room_code
            room = yield room_code.room

            # Room Deassign Course
            if is_teacher and \
                    user.course_id is not None and \
                    user.instances == 1:
                yield room.deassign_course(user.course_id)

            # Leave seat
            if is_student and not self.dont_leave_seat:
                yield room.leave_seat(room_code.seat_id)

        except AttributeError:
            if not hasattr(self.handler, 'room_code') or \
                    self.handler.room_code is None:
                msg.code_warning(
                    msg.join_path(
                        __name__, self.end.__qualname__),
                    "room_code wasn't initialized at "
                    "{.__class__.__name__}'s "
                    "end.".format(self)
                )

            else:
                raise

    @coroutine
    def end(self):
        try:
            yield super().end()

            if not self.session_start_ok:
                return

            if self.user_state_at_exclusive_login:
                user = User(
                    self.user_state_at_exclusive_login)
            else:
                user = self.handler.user
                yield user.sync('instances')

            is_teacher = (user.status == 'room')
            is_student = (user.status == 'seat')

            # Room Deassign Course
            # Leave seat
            yield self.end_room_usage(
                user, is_teacher, is_student)

            # User Deassign Course
            yield user.deassign_course(
                if_last_instance=is_teacher)

            # Decrease Instances
            # (can modify status and course_id)
            yield user.decrease_instances()

        except:
            raise
