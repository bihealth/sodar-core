/* Category statistics retrieval for ProjectDetailView */

$(document).ready(function () {
  let projectUuid = $('#sodar-pr-page-container-detail').attr(
    'data-project-uuid')
  let statsUrl = '/project/ajax/stats/category/' + projectUuid
  $.ajax({
    url: statsUrl,
    method: 'GET',
  }).done(function (data) {
    $('#sodar-pr-details-card-stats-loading').hide()
    if ('stats' in data && data.stats.length) {
      let deck = $('#sodar-pr-details-card-stats-deck')
      let stats = data.stats
      for (let i = 0; i < stats.length; i++) {
        let value = stats[i].value
        if (stats[i].unit) {
          value +=
            '<span class="sodar-pr-dashboard-card-stats-unit">' + stats[
              i].unit + '</span>'
        }
        deck.append(
          $('<div>')
          .attr('class',
            'card mr-0 mb-3 sodar-dashboard-card sodar-pr-dashboard-card-stats'
          )
          .attr('title', stats[i].description)
          .append($('<div>')
            .attr('class', 'card-body')
            .append($('<span>')
              .attr('class', 'pull-right')
              .append($('<i>')
                .attr('class', 'iconify text-info')
                .attr('data-icon', stats[i].icon)
              )
            )
            .append($('<p>')
              .attr('class', 'mb-1')
              .text(stats[i].title)
            )
            .append($('<div>')
              .attr('class', 'text-center')
              .append($('<span>')
                .attr('class', 'sodar-pr-dashboard-card-stats-value')
                .html(value)
              )
            )
          )
        )
      }
    }
  })
})
