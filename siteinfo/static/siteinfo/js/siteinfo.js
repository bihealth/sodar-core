$(document).ready(function () {
  $.get('ajax/stats').done(function (res) {
    let cards = []
    for (const [pluginName, pluginData] of Object.entries(res)) {
      let card = $('<div>').attr({
        'class': 'card sodar-si-app-stats-card',
        'data-plugin-name': pluginName,
      })
      let cardHeader = $('<div>').attr('class', 'card-header').append(
        $('<h4>').append([
          $('<i>').attr({
            'class': 'iconify',
            'data-icon': pluginData.icon,
          }),
          pluginData.title + ' Statistics',
        ])
      )
      let cardBody = $('<div>').attr('class', 'card-body')
      if ('stats' in pluginData) {
        for (const [_, stat] of Object.entries(pluginData.stats)) {
          let statValue = ''
          if ('url' in stat) {
            statValue = $('<dd>').attr('class', 'col-md-9').append(
              $('<a>').attr('href', stat.url).text(stat.value)
            )
          } else {
            statValue = $('<dd>').attr('class', stat.info_cls).append(
              stat.info_val
            )
          }
          cardBody.append(
            $('<dl>').attr('class', 'row').append([
              $('<dt>').attr('class', 'col-md-3').append(
                `${ stat.label } ${ stat?.info_link }`
              ),
              statValue,
            ])
          )
        }
      } else if ('error' in pluginData) {
        cardBody.append(
          $('<div>').attr('class', 'text-danger').text(
            `Unable to retrieve app statistics: ${ pluginData.error }`
          )
        )
      } else {
        console.error(
          `Unexpected response format for plugin ${ pluginName }.`)
        console.dir(pluginData)
      }
      card.append([cardHeader, cardBody])
      cards.push(card)
    }
    $('#sodar-si-app-stats-loading').replaceWith(cards)
  }).fail(function (err) {
    console.error('Unable to fetch app stats: ' + err)
    $('#sodar-si-app-stats-loading').replaceWith(
      $('<div>').attr({
        'class': 'text-center',
        'id': 'sodar-si-app-stats-error',
      }).append([
        $('<i>').attr({
          'class': 'iconify text-secondary',
          'dataIcon': 'mdi:alert-circle',
          'dataHeight': '48'
        }),
        $('<p>').text(
          'There was a problem fetching the app stats, please try again later.'
        ),
      ])
    )
  })
})
