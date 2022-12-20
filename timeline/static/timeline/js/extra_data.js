$(document).ready(function() {
    $('.sodar-tl-link-extra-data').click(function () {
        $('#sodar-modal-wait').modal('show');
        $.ajax({
            url: $(this).attr('data-url'),
            method: 'GET',
        }).done(function (data) {
            $('.modal-title').text(
                'Event extra data: ' + 'Application "' + data['app'] + '" made by ' + data['user']);
            $('.modal-body').html('').append($('<table>')
                .attr('class', 'table table-striped sodar-extra-card-table')
                .attr('id', 'sodar-tl-table-extra-data')
                .append($('<thead>')
                    .append($('<tr>')
                        .append($('<th>').html('Extra data'))
                    )
                )
                .append($('<tbody>'))
            );
            var tableBody = $('.modal-body').find('tbody');
            tableBody.append($('<tr>')
                .append($('<td>').html(JSON.stringify(data['extra']), null, 4))
            );
            $('#sodar-modal-wait').modal('hide');
            $('#sodar-modal').modal('show');
        }).fail(function (data) {
            $('.modal-body').html('Error in extra: ' + data);
            $('#sodar-modal-wait').modal('hide');
            $('#sodar-modal').modal('show');
        });
    });
});