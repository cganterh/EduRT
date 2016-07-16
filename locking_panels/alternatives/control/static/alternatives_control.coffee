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


draw_plot = (newSVG,percent) ->
  l = [
    'A'
    'B'
    'C'
    'D'
    'E'
    'F'
    'G'
    'H'
    'I'
    'J'
    'K'
    'L'
    'M'
    'N'
    'O'
    'P'
    'Q'
    'R'
    'S'
    'T'
    'U'
    'V'
    'W'
    'X'
    'Y'
    'Z'
  ]
  cuenta = newSVG.childElementCount/3
  if cuenta < percent.length
    maxelement = Math.max.apply(Math, percent)
    newSVG.setAttribute 'width', 10 + 50 * percent.length
    newSVG.setAttribute 'height', 160
    rectangulo = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
    rectangulo.setAttribute 'x', '0'
    rectangulo.setAttribute 'height', 100
    rectangulo.setAttribute 'y', 30
    rectangulo.setAttribute 'width', '30'
    rectangulo.style.setProperty 'fill', '#e21e3a'
    texto1 = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    texto1.setAttribute 'x', '0'
    texto1.setAttribute 'y', '150'
    texto1.setAttribute 'fill', 'black'
    texto1.setAttribute 'font-size', '15'
    texto1.setAttribute 'font-family', 'sans-serif'
    texto1.setAttribute 'opacity', '0.7'
    texto1.textContent = ''
    texto2 = texto1.cloneNode(true)
    texto2.textContent = ''
    i = cuenta
    while i < percent.length
      n = percent[i]
      rectangulo.setAttribute 'x', 10 + 40 * i
      if p == maxelement
        rectangulo.style.setProperty 'fill', '#e21e3a'
      else
        rectangulo.style.setProperty 'fill', '#7878d7'
      texto1.textContent = String(n) + '%'
      texto2.textContent = l[i]
      texto1.setAttribute 'x', 10 + 40 * i
      texto1.setAttribute 'y', 20
      texto2.setAttribute 'x', 10 + 40 * i
      newSVG.appendChild rectangulo.cloneNode(true)
      newSVG.appendChild texto1.cloneNode(true)
      newSVG.appendChild texto2.cloneNode(true)
      i++
    delay = (ms, func) -> setTimeout func, ms
    delay 100, -> draw_plot newSVG, percent
  else if cuenta > percent.length
    newSVG.removeChild(newSVG.lastChild);
    newSVG.removeChild(newSVG.lastChild);
    newSVG.removeChild(newSVG.lastChild);
    newSVG.setAttribute 'width', 10 + 50 * percent.length
    draw_plot newSVG, percent
  else
    graficos = newSVG
    elementcount = percent.length
    rectangulos = graficos.querySelectorAll("rect")
    textos = graficos.querySelectorAll("text")
    maxelement = Math.max.apply(Math, percent)
    n = 0
    i = 0
    while n < elementcount
      p = percent[n]
      rectangulo = rectangulos[n]
      texto1 = textos[i]
      texto2 = textos[i+1]
      texto1.textContent = String(p) + '%'
      if p == maxelement
        rectangulo.style.setProperty 'fill', '#e21e3a'
      else
        rectangulo.style.setProperty 'fill', '#7878d7'
      rectangulo.style.setProperty 'transform-origin', 'center 130px 0px'
      a = rectangulo.style.transform.substring(10, 7)
      a *= 100
      t = String(Math.round(3 * Math.abs(a - p) / 10) / 10)
      rectangulo.style.setProperty 'transition', 'transform ' + t + 's linear'
      rectangulo.style.setProperty 'transform', 'scaleY(' + String(p / 100) + ')'
      texto1.style.setProperty 'transition', 'transform ' + t + 's linear'
      texto1.style.setProperty 'transform', 'translateY(' + String((100 - p)*0.115) + 'vh)'
      n++
      i += 2
  return

terminate_alternatives = ->
  ws.sendJSON 'type': 'alternatives.close.teacher'
  return

showAlternativesControl = (message) ->
  if active_panel == 'remote-panel'
    switchToPanel 'alternatives-control-panel'
  else if active_panel == 'presentation-panel'
    alternativesResult = document.querySelector('#presentation_plot')
    alternativesResult = alternativesResult.content.querySelector('div')
    addNodeToPresentation alternativesResult, false
    showhide_button = document.querySelector('.toggle-button')
    showhide_button.addEventListener 'click', alternatives_results_toggleGraphs
  alts_number = message.percentages.length
  plot_init = new Array(alts_number+1).join('0').split('')
  draw_plot plot_init
  return

endAlternatives = ->
  if active_panel == 'alternatives-control-panel'
    switchToPanel 'remote-panel'
  else if active_panel == 'presentation-panel'
    results = document.querySelector(".alternatives.results")
    panel = document.querySelector("#presentation-panel")
    box = panel.querySelector("#presentation-box")
    box.removeChild(results)

showhide = ->
  showhide_button = document.getElementById('showhide')
  text = showhide_button.querySelector('span')
  if text.textContent == 'Mostrar Gráficos'
    text.textContent = 'Ocultar Gráficos'
    showhide_button.classList.remove('show')
    showhide_button.classList.add('hide')
    #ws.sendJSON 'type': 'alternatives.results.show'
  else
    text.textContent = 'Mostrar Gráficos'
    showhide_button.classList.remove('hide')
    showhide_button.classList.add('show')
    #ws.sendJSON 'type': 'toFrontend', 'content' : 'type':'alternatives.results.hide'

alternatives_results_showGraphs = ->
  if active_panel == 'presentation-panel'
    panel = document.querySelector(".alternatives.results")
    panel.classList.remove("closed")
    panel.classList.add("opened")

alternatives_results_hideGraphs = ->
  if active_panel == 'presentation-panel'
    panel = document.querySelector(".alternatives.results")
    panel.classList.add("closed")
    panel.classList.remove("opened")


alternatives_results_toggleGraphs = ->
  if active_panel == 'presentation-panel'
    panel = document.querySelector(".alternatives.results")
    if panel.classList.contains("closed")
      panel.classList.remove("closed")
      panel.classList.add("opened")
    else
      panel.classList.add("closed")
      panel.classList.remove("opened")



showhide_button = document.getElementById('showhide')
showhide_button.addEventListener 'click', showhide

showhide_button = document.getElementById('terminate')
showhide_button.addEventListener 'click', terminate_alternatives


ws.addMessageListener 'alternatives.results', (m) ->
  draw_plot svg, m.percentages for svg in document.querySelectorAll(".alternatives.plot")
  return

ws.addMessageListener(
  'alternatives.show', showAlternativesControl)
ws.addMessageListener(
  'alternatives.results.show',
  alternatives_results_showGraphs )
ws.addMessageListener(
 'alternatives.results.hide',
  alternatives_results_hideGraphs )
ws.addMessageListener(
 'alternatives.close.clients',
 endAlternatives )
