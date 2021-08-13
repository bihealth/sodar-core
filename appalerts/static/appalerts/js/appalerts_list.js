$(document).ready(function () {
    // Handle alert dismissal
    $('.sodar-app-alert-btn-dismiss').click(function () {
        var uuid = $(this).attr('data-uuid');
        var clearCount = 1;
        $.post({
            url: $(this).attr('data-dismiss-url'),
            method: 'POST',
            dataType: 'json'
        }).done(function (data) {
          if (uuid) { // Hide single alert if UUID is found
              $(document).find("[data-alert-uuid='" + uuid + "']").fadeOut(250);
          } else { // Hide all
              var alerts = $(document).find('.sodar-app-alert-item');
              clearCount = alerts.length;
              alerts.each(function () {
                  $(this).fadeOut(250);
              });
          }
          // Update/hide title bar badge
          var alertCount = $(document).find('#sodar-app-alert-count');
          var alertCountInt = parseInt($(document).find(
              '#sodar-app-alert-count').html()) - clearCount;
          var alertLegend = $(document).find('#sodar-app-alert-legend');
          if (alertCountInt <= 0) {
              $(document).find('#sodar-app-alert-badge').fadeOut(250);
          } else {
              alertCount.html(alertCountInt.toString());
              if (alertCountInt === 1) {
                  alertLegend.html('alert')
              } else alertLegend.html('alerts')
          }
        }).fail(function () {
            if (uuid) {
              console.error('Unable to dismiss alert (UUID=' +
                  $(this).attr('data-uuid') + ')');
            } else {
              console.error('Unable to dismiss alerts');
            }
        });
    });
});
