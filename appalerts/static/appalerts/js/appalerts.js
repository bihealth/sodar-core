// Update alert status
var updateAlertStatus = function () {
  var alertNav = $(document).find('#sodar-app-alert-nav');
  if (alertNav) {
    $.ajax({
        url: alertNav.attr('data-status-url'),
        method: 'GET',
        dataType: 'json'
    }).done(function (data) {
      var alertBadge = alertNav.find('#sodar-app-alert-badge');
      alertBadge.find('#sodar-app-alert-count').html(data['alerts']);
      var legend = alertBadge.find('#sodar-app-alert-legend');
      if (data['alerts'] > 0) {
          $(document).find('#sodar-app-alert-badge').show();
          if (data['alerts'] === 1) legend.html('alert');
          else legend.html('alerts');
      } else $(document).find('#sodar-app-alert-badge').fadeOut(250);
    });
  }
};

$(document).ready(function() {
    var alertNav = $(document).find('#sodar-app-alert-nav');
    if (alertNav) {
        var alertInterval = $(document).find(
            '#sodar-app-alert-nav').attr('data-interval');
        // Update user alerts
        setInterval(function () {
            updateAlertStatus();
        }, alertInterval * 1000);
    }
});

// Handle alert dismissal
$(document).ready(function () {
    $('.sodar-app-alert-btn-dismiss').click(function () {
        var uuid = $(this).attr('data-uuid');
        $.post({
            url: $(this).attr('data-dismiss-url'),
            method: 'POST',
            dataType: 'json'
        }).done(function (data) {
          // Hide alert
          $(document).find("[data-alert-uuid='" + uuid + "']").fadeOut(250);
          // Update/hide title bar badge
          var alertCount = $(document).find('#sodar-app-alert-count');
          var alertCountInt = parseInt($(document).find(
              '#sodar-app-alert-count').html()) - 1;
          var alertLegend = $(document).find('#sodar-app-alert-legend');
          if (alertCountInt === 0) {
              $(document).find('#sodar-app-alert-badge').fadeOut(250);
          } else {
              alertCount.html(alertCountInt.toString());
              if (alertCountInt === 1) {
                  alertLegend.html('alert')
              } else alertLegend.html('alerts')
          }
        }).fail(function () {
            console.error('Unable to dismiss alert (UUID=' +
                $(this).attr('data-uuid') + ')');
        });
    });
});
