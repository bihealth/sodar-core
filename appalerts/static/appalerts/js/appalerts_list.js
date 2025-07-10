function updateEmptyAlertsElement() {
  let alertBadge = $(document).find('#sodar-app-alert-badge')
  let emptyElem = $(document).find('#sodar-app-alert-empty')

  if (emptyElem && emptyElem.is(':visible') && alertBadge.is(':visible')) {
    emptyElem.html(
      '<a href="#" id="sodar-app-alert-reload" ' +
      'onclick="window.location.reload()">' +
      'Please reload this page to view new alerts.</a>')
  }
}

$(document).ready(function () {
  // Handle alert dismissal
  $('.sodar-ap-btn-dismiss').click(function () {
    let uuid = $(this).attr('data-uuid')
    let clearCount = 1
    $.post({
      url: $(this).attr('data-dismiss-url'),
      method: 'POST',
      dataType: 'json'
    }).done(function (data) {
      if (uuid) { // Hide single alert if UUID is found
        $(document).find("[data-alert-uuid='" + uuid + "']")
          .fadeOut(250)
      } else { // Hide all
        let alerts = $(document).find('.sodar-app-alert-item')
        clearCount = alerts.length
        alerts.each(function () {
          $(this).fadeOut(250)
        })
      }
      // Update/hide title bar badge and no alerts message
      let alertCount = $(document).find('#sodar-app-alert-count')
      let alertCountInt = parseInt($(document).find(
        '#sodar-app-alert-count').html()) - clearCount
      let alertLegend = $(document).find('#sodar-app-alert-legend')
      if (alertCountInt <= 0) {
        $(document).find('#sodar-app-alert-badge').fadeOut(250)
        $(document).find('#sodar-app-alert-empty').delay(300)
          .fadeIn(250)
        $(document).find('#sodar-ap-ops-dismiss-all').addClass(
          'disabled')
      } else {
        alertCount.html(alertCountInt.toString())
        if (alertCountInt === 1) {
          alertLegend.html('alert')
        } else alertLegend.html('alerts')
      }
    }).fail(function () {
      if (uuid) {
        console.error('Unable to dismiss alert (UUID=' +
          $(this).attr('data-uuid') + ')')
      } else {
        console.error('Unable to dismiss alerts')
      }
    })
  })

  // Update empty alerts element
  let alertNav = $(document).find('#sodar-app-alert-nav')
  if (alertNav) {
    let alertInterval = $(document).find(
      '#sodar-app-alert-nav').attr('data-interval')
    // Update user alerts
    setInterval(function () {
      updateEmptyAlertsElement()
    }, alertInterval * 1000)
  }
})
