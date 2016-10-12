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


#VARIABLES
alternatives_form = document.getElementById 'alternatives_form'
get_span = null
template = null
template_content = null
template_content_input = null
template_content_label = null
template_clone = null
question_data = null
alternatives_form_name_single = null

#FUNCTIONS
@addWording = (text) ->
  alternatives_form.textContent = text

@addAlternative = (index, text) ->
  template = document.getElementById 'alternatives_template'
  get_span = template.content.querySelector 'span'
  template_content = template.content
  template_content_input = template.content.querySelector 'input'
  template_content_label = template.content.querySelector 'label'
  template_content_input.value = index
  get_span.textContent = text
  template_clone = document.importNode template_content, true
  alternatives_form.appendChild template_clone

#SETUP
ws.addMessageListener 'alternatives.show', (message) ->
  addWording message.wording
  addAlternative index, text for text, index in message.answers
  alternatives_form.addEventListener 'change', ->
    ws.sendJSON {'type':'alternatives.answer', \
    'alternative':parseInt(alternatives_form.alternatives_answer.value)}
