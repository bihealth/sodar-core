// Project list filtering
$(document).ready(function () {
    $('#sodar-pr-home-display-notfound').hide();
    $('#sodar-pr-home-display-nostars').hide();

    // Filter input
    $('#sodar-pr-project-list-filter').keyup(function () {
        var v = $(this).val().toLowerCase();
        var valFound = false;
        $('#sodar-pr-home-display-nostars').hide();

        if (v.length > 2) {
            $('.sodar-pr-home-display-default').hide();
            $('#sodar-pr-project-list-filter').removeClass('text-danger').addClass('text-success');
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star-outline"></i> Starred');

            $('.sodar-pr-project-list-item').each(function () {
                var fullTitle = $(this).attr('data-full-title');
                var titleLink = $(this).find('td:first-child div span.sodar-pr-project-title a');

                if (titleLink && fullTitle.toLowerCase().indexOf(v) !== -1) {
                    $(this).find('.sodar-pr-project-indent').hide();
                    // Reset content for updating the highlight
                    titleLink.html(fullTitle);
                    // Highlight
                    var pattern = new RegExp("(" + v + ")", "gi");
                    var titlePos = fullTitle.toLowerCase().indexOf(v);
                    if (titlePos !== -1) {
                        var titleVal = fullTitle.substring(titlePos, titlePos + v.length);
                        titleLink.html(fullTitle.replace(
                            pattern, '<span class="sodar-search-highlight">' + titleVal + '</span>'));
                    }
                    $(this).show();
                    valFound = true;
                    $('#sodar-pr-home-display-notfound').hide();
                } else {
                    $(this).hide();
                }
            });
            if (valFound === false) {
                $('#sodar-pr-home-display-notfound').show();
            }
        } else {
            $('.sodar-pr-project-list-item').each(function () {
                var anchor = $(this).find('a.sodar-pr-project-link');
                var title = $(this).attr('data-title');
                if (anchor) anchor.text(title);
                else $(this).find('span.sodar-pr-project-title').text(title);
                $(this).show();
                $(this).find('.sodar-pr-project-indent').show();
            });
            $('#sodar-pr-home-display-notfound').hide();
            $('#sodar-pr-project-list-filter').addClass(
                'text-danger').removeClass('text-success');
            $('#sodar-pr-project-list-link-star').attr('data-filter-mode', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });

    // Filter by starred
    $('#sodar-pr-project-list-link-star').click(function () {
        $('#sodar-pr-home-display-notfound').hide();
        $('#sodar-pr-project-list-filter').val('');

        if ($(this).attr('data-filter-mode') === '0') {
            var starCount = 0;
            $('.sodar-pr-project-list-item').each(function () {
                if ($(this).attr('data-starred') === '1') {
                  $(this).find('.sodar-pr-project-indent').hide();
                  $(this).find('a.sodar-pr-project-link').text($(this).attr('data-full-title'));
                  $(this).show();
                  starCount += 1;
                } else $(this).hide();
            });
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star"></i> Starred');
            $(this).attr('data-filter-mode', '1');
            if (starCount === 0) {
                $('#sodar-pr-home-display-nostars').show();
            }
        } else if ($(this).attr('data-filter-mode') === '1') {
            $('#sodar-pr-home-display-nostars').hide();
            $('.sodar-pr-project-list-item').each(function () {
                $(this).find('.sodar-pr-project-indent').show();
                $(this).find('a.sodar-pr-project-link').text($(this).attr('data-title'));
                $(this).show();
            });
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star-outline"></i> Starred');
            $(this).attr('data-filter-mode', '0');
        }

        // Update overflow status
        modifyCellOverflow();
    });
});

// Function for updating custom columns
function updateCustomColumns (projectUuids) {
    // Grab column app names and IDs from header into a list
    var colIds = [];
    $('.sodar-pr-project-list-custom-header').each(function () {
        colIds.push({
            app: $(this).attr('data-app-name'),
            id: $(this).attr('data-column-id')
        });
    });
    if (colIds.length === 0) return; // Skip if no columns were found

    // Retrieve column data
    $.ajax({
        url: $('.sodar-pr-project-list-header').attr('data-custom-col-url'),
        method: 'POST',
        dataType: 'json',
        contentType : 'application/json',
        data: JSON.stringify({'projects': projectUuids})
    }).done(function (data) {
        // Update columns
        $('.sodar-pr-project-list-item-project').each(function () {
            var projectData = data[$(this).attr('data-uuid')];
            var i = 0;
            $(this).find('.sodar-pr-project-list-custom').each(function () {
                $(this).html(projectData[colIds[i].app][colIds[i].id].html);
                i += 1;
            });
        });
    });
}

// Function for updating role column
function updateRoleColumn (projectUuids) {
    // TODO: Do ajax request, update column
}

// Retrieve project list data
$(document).ready(function () {
    var table = $('#sodar-pr-project-list-table');
    var listUrl = table.attr('data-url');
    var parentUuid = table.attr('data-parent');
    var customColAlign = [];
    $('.sodar-pr-project-list-custom-header').each(function () {
        customColAlign.push($(this).attr('data-align'));
    });
    var colCount = customColAlign.length + 2;
    $.ajax({
        url: listUrl,
        method: 'GET',
    }).done(function (data) {
        $('#sodar-pr-project-list-loading').remove();
        var tableBody = $('#sodar-pr-project-list-table tbody');

        // If there are no results, display message row
        if (data.projects.length === 0) {
            tableBody.append($('<tr>')
                .append($('<td>')
                    .attr('colspan', colCount)
                    .attr('class', 'text-center text-muted font-italic')
                    .text(data['messages']['no_projects'])
                )
            );
            return;
        }

        // Display rows
        $('#sodar-pr-project-list-table').addClass('sodar-card-table-borderless');

        for (var i = 0; i < data.projects.length; i++) {
            var p = data.projects[i];
            var icon;
            var titleClass = '';
            if (p.type === 'CATEGORY') {
                icon = 'rhombus-split';
                titleClass = 'text-underline';
            } else icon = 'cube';

            // Row
            tableBody.append($('<tr>')
                .attr('class',
                    'sodar-pr-project-list-item sodar-pr-project-list-item-' +
                    p.type.toLowerCase())
                .attr('id', 'sodar-pr-project-list-item-' + p.uuid)
                .attr('data-uuid', p.uuid)
                .attr('data-title', p.title)
                .attr('data-full-title', p['full_title'])
                .attr('data-starred', + p['starred'])
            );
            var row = tableBody.find('tr:last');

            // Title column
            row.append($('<td>')
                .append($('<div>')
                .attr('class', 'sodar-overflow-container')
                    .append($('<span>')
                        .attr('class', 'sodar-pr-project-indent')
                        .attr('style', 'padding-left: ' +
                            (p.depth - data['parent_depth']) * 25 + 'px;')
                        .append($('<i>')
                            .attr('class', 'iconify mr-1')
                            .attr('data-icon', 'mdi:' + icon))
                        .append($('<span>')
                            .attr('class', 'sodar-pr-project-title ' + titleClass)
                            .append($('<a>')
                                .attr('href', '/project/' + p.uuid)
                                .html(p.title)
                            )
                        )
                    )
                )
            );

            // Add icons to title columns
            var titleSpan = row.find($('span.sodar-pr-project-title'));
            // Remote icon
            if (p.remote) {
                var textClass;
                if (p.revoked) textClass = 'text-danger';
                else textClass = 'text-info';
                titleSpan.append($('<i>')
                    .attr('class', 'iconify text-info ml-2 sodar-pr-remote-project-icon ' + textClass)
                    .attr('data-icon', 'mdi:cloud')
                    .attr('title', 'Remote synchronized from source site')
            );
            }
            // Public icon
            if (p.type === 'PROJECT' && p.public_guest_access) {
                titleSpan.append($('<i>')
                    .attr('class', 'iconify text-info ml-2 sodar-pr-project-public')
                    .attr('data-icon', 'mdi:earth')
                    .attr('title', 'Public guest access')
                );
            }
            // Starred icon
            if (p.starred) {
                titleSpan.append($('<i>')
                    .attr('class', 'iconify text-warning ml-2 sodar-tag-starred')
                    .attr('data-icon', 'mdi:star')
                );
            }

            // Fill project custom columns with spinners
            for (var j = 1; j < colCount - 1; j++) {
                if (p.type === 'PROJECT') {
                    row.append($('<td>')
                        .attr('class', 'sodar-pr-project-list-custom text-' + customColAlign[j - 1])
                        .append($('<i>')
                            .attr('class', 'iconify spin text-muted')
                            .attr('data-icon', 'mdi:loading')
                        )
                    );
                } else row.append($('<td>'));
            }
            // Add user role column
            row.append($('<td>')
                .append($('<i>')
                    .attr('class', 'iconify spin text-muted')
                    .attr('data-icon', 'mdi:loading')
                )
            );
        }

        // Enable starred button and filter
        $('#sodar-pr-project-list-link-star').prop('disabled', false);
        $('#sodar-pr-project-list-filter').prop('disabled', false);

        // Get project UUIDs (skip categories)
        var projectUuids = [];
        $('.sodar-pr-project-list-item-project').each(function () {
            projectUuids.push($(this).attr('data-uuid'));
        });
        if (projectUuids.length > 0) {
            // Update custom columns
            updateCustomColumns(projectUuids);
            // Update role column
            updateRoleColumn(projectUuids);
        }
    });
});
