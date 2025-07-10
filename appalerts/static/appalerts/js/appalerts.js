// Update alert status
let updateAlertStatus = function () {
  let alertNav = $(document).find('#sodar-app-alert-nav')
  let statusUrl = alertNav.attr('data-status-url')
  if (statusUrl) {
    $.ajax({
      url: statusUrl,
      method: 'GET',
      dataType: 'json'
    }).done(function (data) {
      let alertBadge = alertNav.find('#sodar-app-alert-badge')
      alertBadge.find('#sodar-app-alert-count').html(data['alerts'])
      let legend = alertBadge.find('#sodar-app-alert-legend')
      if (data['alerts'] > 0) {
        $(document).find('#sodar-app-alert-badge').show()
        if (data['alerts'] === 1) legend.html('alert')
        else legend.html('alerts')
      } else $(document).find('#sodar-app-alert-badge').fadeOut(250)
    })
  }
}

$(document).ready(function () {
  // Set up alert updating
  let alertNav = $(document).find('#sodar-app-alert-nav')
  if (alertNav) {
    let alertInterval = $(document).find(
      '#sodar-app-alert-nav').attr('data-interval')
    // Update user alerts
    setInterval(function () {
      updateAlertStatus()
    }, alertInterval * 1000)
  }

  // Handle alert dismissal
  $('#sodar-app-alert-badge-dismiss').click(function () {
    $.post({
      url: $(this).attr('data-dismiss-url'),
      method: 'POST',
      dataType: 'json'
    }).done(function () {
      // If we are on the alert list, update it accordingly
      let alerts = $(document).find('.sodar-app-alert-item')
      if (alerts.length > 0) {
        alerts.each(function () {
          $(this).fadeOut(250)
        })
        $(document).find('#sodar-app-alert-empty').delay(300)
          .fadeIn(250)
        $(document).find('#sodar-ap-ops-dismiss-all').addClass(
          'disabled')
      }
      // Fade the badge itself
      $(document).find('#sodar-app-alert-badge').fadeOut(250)
    }).fail(function (err) {
      console.error('Unable to dismiss alerts: ' + err)
    })
  })
})
