var extra_data = function () {
        var dataUrl = $(this).attr('data-url');
        $('#sodar-modal').modal('hide');
        $('#sodar-modal-wait').modal('show');
        $.ajax({
            url: dataUrl,
            method: 'GET',
        }).done(function (data) {
            $('.modal-title').text(
                'Event Extra Data: ' + data['app'] + '.' + data['name'] + ' (' +
                data['user'] + ' @ ' + data['timestamp'] + ')');
            $('.modal-body').html('').append($('<p>').html(
                '<pre class="sodar-tl-json" id=data-to-clipboard>' + data['extra'] + '</pre>'));
            $('#sodar-modal-wait').modal('hide');
            $('#sodar-modal').modal('show');
        }).fail(function (data) {
            console.dir(data);
            $('.modal-body').html('Error: ' + data.statusText);
            $('#sodar-modal-wait').modal('hide');
            $('#sodar-modal').modal('show');
        });
    };
$(document).ready(function() {
    $('.sodar-tl-link-detail').click(function () {
        $('#sodar-modal-wait').modal('show');
        $.ajax({
            url: $(this).attr('data-url'),
            method: 'GET',
        }).done(function (data) {
            $('.modal-title').text(
                'Event Details: ' + data['app'] + '.' + data['name'] + ' (' +
                data['user'] + ' @ ' + data['timestamp'] + ')');
            $('.modal-body').html('').append($('<table>')
                .attr('class', 'table table-striped sodar-card-table')
                .attr('id', 'sodar-tl-table-detail')
                .append($('<thead>')
                    .append($('<tr>')
                        .append($('<th>').html('Timestamp'))
                        .append($('<th>').html('Description'))
                        .append($('<th>').html('Status'))
                    )
                )
                .append($('<tbody>'))
            );
            var tableBody = $('.modal-body').find('tbody');
            for (var i = 0; i < data['status'].length; i++) {
                let extraData = '<a class="sodar-tl-link-status-extra-data text-primary pull-right" ' +
                    'data-url="' + data['status'][i]['extra_status_link'] + '"><i class="iconify" ' +
                    'data-icon="mdi:text-box" title="Status Extra Data" data-toggle="tooltip" data-placement="right">' +
                    '</i></a>';
                if (data['status'][i]['extra_status_link'] === null) {
                    extraData = '';
                }
                tableBody.append($('<tr>')
                    .append($('<td>').html(data['status'][i]['timestamp']))
                    .append($('<td>').html(data['status'][i]['description'] + extraData))
                    .append($('<td>')
                        .attr('class', data['status'][i]['class'])
                        .html(data['status'][i]['type'])
                    )
                );
            }
            $('#sodar-modal-wait').modal('hide');
            $('#sodar-modal').modal('show');
        }).fail(function (data) {
            console.dir(data);
            $('.modal-body').html('Error: ' + data.statusText);
            $('#sodar-modal-wait').modal('hide');
            $('#sodar-modal').modal('show');
        });
    });
    $('.sodar-tl-link-extra-data').click(extra_data);
});
$('body').on('click', '.sodar-tl-link-status-extra-data', extra_data);