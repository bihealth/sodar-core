$(document).ready(function () {
  $.get('ajax/stats').done(function (res) {
    let cards = [];
    for (const [plugin_id, plugin] of Object.entries(res)) {
      let stats = [];
      if ('stats' in plugin) {
        for (const [_, stat] of Object.entries(plugin.stats)) {
          let info_link = '';
          let stat_url = '';
          if ('info_link' in stat) {
            info_link = stat.info_link;
          }
          if ('url' in stat) {
            stat_url = `
              <dd class="col-md-9">
                <a href="${ stat.url }">${ stat.value }</a>
              </dd>`;
          } else {
            stat_url = `
              <dd class="${ stat.info_cls }">
                ${ stat.info_val }
              </dd>`;
          }
          stats.push(`
            <dt class="col-md-3">${ stat.label }
              ${ info_link }
            </dt>
            ${ stat_url }
          `);
        }
      } else if ('error' in plugin) {
        stats.push(`
          <dd class="col-md-12 text-danger">
            Unable to retrieve app statistics: ${ plugin.error }
          </dd>
        `);
      } else {
        console.error('Unexpected plugin format from ajax/stats view.')
      }
      cards.push(`
        <div class="card" id="sodar-si-${ plugin_id }-app-stats-card">
          <div class="card-header">
            <h4>
              <i class="iconify" data-icon="${ plugin.icon }"></i>
              ${ plugin.title } Statistics
            </h4>
          </div>
          <div class="card-body">
            <dl class="row">
              ${ stats.join('\n') }
            </dl>
          </div>
        </div>
      `)
    }
    $('#sodar-si-app-stats-loading').replaceWith(cards);
  }).fail(function (err) {
    console.error('Unable to fetch app stats: ' + err);
    $('#sodar-si-app-stats-loading').replaceWith(`
      <div class="text-center" id="sodar-si-app-stats-error">
        <i class="iconify text-secondary"
           data-icon="mdi:alert-circle" data-height="48">
        </i>
        <p>There was a problem fetching the app stats,
           please try again later.</p>
      </div>
    `);
  });
});
