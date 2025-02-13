// Function for updating custom columns
function updateCustomColumns (uuids) {
    // Grab column app names and IDs from header into a list
    var colIds = [];
    $('.sodar-pr-project-list-custom-header').each(function () {
        colIds.push({
            app: $(this).attr('data-app-name'),
            id: $(this).attr('data-column-id')
        });
    });
    if (colIds.length === 0) return; // Skip if no columns were found

    var getAjaxRequest = function (start, end) {
        return $.ajax({
            url: $('.sodar-pr-project-list-table').attr('data-custom-col-url'),
            method: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({'projects': uuids.slice(start, end)})
        })
    };

    // Get datatables table and API
    var dt = $('#sodar-pr-project-list-table').DataTable();
    var dtApi = new $.fn.dataTable.Api('#sodar-pr-project-list-table');
    var start = 0;
    var interval = 25;
    var values = [];
    var dfd = $.Deferred();
    var dfdNext = dfd;
    dfd.resolve();

    // Populate columns with sequential queries
    while (start <= uuids.length) {
        values.push([start, start + interval]);
        dfdNext.pipe(function () {
            var value = values.shift();
            return getAjaxRequest(value[0], value[1]).done(function (data) {
                $.each(data, function (uuid, projectData) {
                    var dtRow = dt.row('#sodar-pr-project-list-item-' + uuid);
                    var rowIdx = dtRow.index();
                    var cIdx = 0;
                    // NOTE: We start at 1 to skip project title cell
                    for (var i = 1; i < dtRow.data().length; i++) {
                        var node = $(dtApi.cell(rowIdx, i).node());
                        var nodeClass = node.attr('class');
                        if (nodeClass &&
                                nodeClass.includes('sodar-pr-project-list-custom')) {
                            dtApi.cell(rowIdx, i).data(
                                projectData[colIds[cIdx].app][colIds[cIdx].id].html);
                            cIdx += 1
                        }
                    }
                });
            });
        });
        start += interval;
    }
}

// Function for updating role column
function updateRoleColumn (uuids) {
    var getAjaxRequest = function (start, end) {
        return $.ajax({
            url: $('.sodar-pr-project-list-table').attr('data-role-url'),
            method: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({'projects': uuids.slice(start, end)})
        })
    };

    var dt = $('#sodar-pr-project-list-table').DataTable();
    var dtApi = new $.fn.dataTable.Api('#sodar-pr-project-list-table');
    var start = 0;
    var interval = 25;
    var values = [];
    var dfd = $.Deferred();
    var dfdNext = dfd;
    dfd.resolve();

    while (start <= uuids.length) {
        values.push([start, start + interval]);
        dfdNext.pipe(function () {
            var value = values.shift();
            return getAjaxRequest(value[0], value[1]).done(function (data) {
                $.each(data, function (uuid, colData) {
                    var dtRow = dt.row('#sodar-pr-project-list-item-' + uuid);
                    var rowIdx = dtRow.index();
                    var colIdx = dtRow.data().length - 1;
                    var node = $(dtApi.cell(rowIdx, colIdx).node());
                    var nodeClass = node.attr('class');
                    if (nodeClass &&
                            nodeClass.includes('sodar-pr-project-list-role')) {
                        dtApi.cell(rowIdx, colIdx).data(colData.name)
                        if (colData.class) {
                            node.attr('class', nodeClass + ' ' + colData.class);
                        }
                    }
                });
            });
        });
        start += interval;
    }
}

// Project list data retrieval and updating
$(document).ready(function () {
    var table = $('#sodar-pr-project-list-table');
    var listUrl = table.attr('data-list-url');
    var customColAlign = [];
    $('.sodar-pr-project-list-custom-header').each(function () {
        customColAlign.push($(this).attr('data-align'));
    });
    var colCount = customColAlign.length + 2;
    var allUuids = [];
    var projectUuids = [];
    var tableBody = $('#sodar-pr-project-list-table tbody');

    $.ajax({
        url: listUrl,
        method: 'GET',
    }).done(function (data) {
        $('#sodar-pr-project-list-loading').remove();
        // If there are no results, display message row
        if (data.projects.length === 0) {
            // var tableBody = $('#sodar-pr-project-list-table tbody');
            tableBody.append($('<tr>')
                .attr('id', 'sodar-pr-project-list-message')
                .append($('<td>')
                    .attr('colspan', colCount)
                    .attr('class', 'text-center text-muted font-italic')
                    .text(data['messages']['no_projects'])
                )
            );
            return;
        }

        // Display rows
        var projectCount = data['projects'].length;
        var starredCount = 0;
        const catDelim = ' / ';

        for (var i = 0; i < projectCount; i++) {
            var p = data['projects'][i];
            var icon;
            var projectType;
            if (p['type'] === 'CATEGORY') {
                icon = 'rhombus-split';
                projectType = 'Category';
            } else {
                icon = 'cube';
                projectType = 'Project';
            }

            // Row
            tableBody.append($('<tr>')
                .attr('class',
                    'sodar-pr-project-list-item sodar-pr-project-list-item-' +
                    p['type'].toLowerCase())
                .attr('id', 'sodar-pr-project-list-item-' + p['uuid'])
                .attr('data-uuid', p['uuid'])
                .attr('data-full-title', p['full_title'])
                .attr('data-starred', + p['starred'])
            );
            if (p['starred']) starredCount += 1;
            var row = tableBody.find('tr:last');

            // Title column
            var p_elem = '<a>';
            var p_href = '/project/' + p['uuid'];
            var p_class = 'sodar-pr-project-link';
            if (!p['access']) {
                p_elem = '<span>';
                p_href = '';
                p_class = 'text-muted sodar-pr-project-link-disabled';
            }
            // Highlight project title in category structure
            var titleHtml = '';
            if (data['user']['highlight'] &&
                    projectType.toUpperCase() === 'PROJECT' &&
                    p['full_title'].includes(catDelim)) {
                var titleSplit = p['full_title'].split(catDelim);
                var splitLen = titleSplit.length;
                titleHtml = titleSplit.slice(0, splitLen - 1).join(catDelim);
                titleHtml += catDelim + '<strong>' + titleSplit[splitLen - 1] +
                    '</strong>';
            } else titleHtml = p['full_title'];
            row.append($('<td>')
                .attr('class', 'sodar-pr-project-list-title-td')
                .append($('<div>')
                .attr('class', 'sodar-pr-project-title-container')
                    .append($('<i>')
                        .attr('class', 'iconify mr-1')
                        .attr('data-icon', 'mdi:' + icon)
                        .attr('title', projectType)
                    )
                    .append($('<span>')
                        .attr('class', 'sodar-pr-project-title')
                        .append($(p_elem)
                            .attr('class', p_class)
                            .attr('href', p_href)
                            .html(titleHtml)
                        )
                    )
                )
            );

            // Add icons to title columns
            var titleSpan = row.find($('span.sodar-pr-project-title'));
            // Remote icon
            if (p['remote']) {
                var textClass;
                if (p['revoked']) textClass = 'text-danger';
                else textClass = 'text-info';
                titleSpan.append($('<i>')
                    .attr('class',
                        'iconify text-info ml-2 sodar-pr-remote-project-icon ' +
                        textClass)
                    .attr('data-icon', 'mdi:cloud')
                    .attr('title', 'Remote synchronized from source site')
            );
            }
            // Public icon
            if (p['type'] === 'PROJECT' && p['public_guest_access']) {
                titleSpan.append($('<i>')
                    .attr('class', 'iconify text-info ml-2 sodar-pr-project-public')
                    .attr('data-icon', 'mdi:earth')
                    .attr('title', 'Public guest access')
                );
            }
            // Archived icon
            if (p['type'] === 'PROJECT' && p['archive']) {
                titleSpan.append($('<i>')
                    .attr('class', 'iconify text-info ml-2 sodar-pr-project-archive')
                    .attr('data-icon', 'mdi:archive')
                    .attr('title', 'Archived')
                );
            }
            // Starred icon
            if (p['starred']) {
                titleSpan.append($('<i>')
                    .attr('class', 'iconify text-warning ml-2 sodar-pr-project-starred')
                    .attr('data-icon', 'mdi:star')
                );
            }
            // Finder link
            if (!p['access'] && p['finder_url']) {
                titleSpan.append($('<a>')
                    .attr('href', p['finder_url'])
                    .attr('class', 'sodar-pr-project-findable')
                    .attr('title', 'Findable project: Request access from ' +
                                   'category owner or delegate')
                    .append($('<i>')
                        .attr('class', 'iconify ml-2')
                        .attr('data-icon', 'mdi:account-supervisor')

                    )
                );
            }

            // Fill project custom columns with spinners
            for (var j = 1; j < colCount - 1; j++) {
                if (p['type'] === 'PROJECT' && p['access']) {
                    row.append($('<td>')
                        .attr('class',
                            'sodar-pr-project-list-custom text-' +
                            customColAlign[j - 1])
                        .append($('<i>')
                            .attr('class', 'iconify spin text-muted ' +
                                'sodar-pr-project-list-load-icon')
                            .attr('data-icon', 'mdi:loading')
                        )
                    );
                } else row.append($('<td>'));
            }
            // Add user role column
            if (!data['user']['superuser'] && p['access']) {
                row.append($('<td>')
                    .attr('class', 'sodar-pr-project-list-role')
                    .append($('<i>')
                        .attr('class', 'iconify spin text-muted ' +
                            'sodar-pr-project-list-load-icon')
                        .attr('data-icon', 'mdi:loading')
                    )
                );
            } else if (!data['user']['superuser']) {
                row.append($('<td>')
                    .attr('class', 'sodar-pr-project-list-role text-muted')
                    .html('N/A')
                );
            }

            // Add categories and projects with access for further queries
            if (p['access']) {
                allUuids.push(p['uuid']);
                if (p['type'] === 'PROJECT') {
                    projectUuids.push(p['uuid']);
                }
            }
        }

        // Enable starred button and filter
        if (starredCount > 0 && starredCount < projectCount) {
            $('#sodar-pr-project-list-link-star').prop('disabled', false);
        }
        if (projectCount > 1) {
            $('#sodar-pr-project-list-filter').prop('disabled', false);
        }

        // Enable datatables
        $.fn.dataTable.ext.classes.sPageButton =
            'btn sodar-list-btn ml-1 sodar-paginate-button btn-outline-light ' +
            'text-primary';
        var dt = $('#sodar-pr-project-list-table').DataTable({
            ordering: false,
            scrollX: false,
            paging: true,
            pageLength: window.projectListPagination,
            lengthChange: true,
            scrollCollapse: true,
            info: false,
            language: {
                paginate: {
                    previous: '<i class="iconify text-primary" ' +
                        'data-icon="mdi:arrow-left-circle"></i> Prev',
                    next: '<i class="iconify text-primary" ' +
                        'data-icon="mdi:arrow-right-circle"></i> Next'
                }
            },
            dom: 'tp'
        });
        // Hide pagination if only one page
        if (dt.page.info().pages === 1) {
            // TODO: Disable pagination control once implemented
            $('.dataTables_paginate').hide();
        }
        // Add star filter
        $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex, rowObj, counter) {
            var api = new $.fn.dataTable.Api('#sodar-pr-project-list-table');
            var filterEnabled = $('#sodar-pr-project-list-link-star')
                .attr('data-star-enabled');
            if (filterEnabled === '1') {
                return $(api.row(dataIndex).node()).data('starred');
            } else return true;
        });
        // Handle page length change
        $('#sodar-pr-project-list-page-length').change(function () {
            var dt = $(this).closest(
                '#sodar-pr-project-list').find('table').DataTable();
            var value = parseInt($(this).val());
            dt.page.len(value).draw();
            // Update user setting
            $.ajax({
                url: 'project/api/settings/set/user',
                method: 'POST',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    'plugin_name': 'projectroles',
                    'setting_name': 'project_list_pagination',
                    'value': value
                })
            })
        });

        if (projectUuids.length > 0) {
            // Update custom columns
            updateCustomColumns(projectUuids);
        }
        if (allUuids.length > 0) {
            // Update role column
            if (!data['user']['superuser']) {
                updateRoleColumn(allUuids);
            }
        }
    });
});

// Project list filtering
$(document).ready(function () {
    // Filter input
    $('#sodar-pr-project-list-filter').keyup(function () {
        var starBtn = $('#sodar-pr-project-list-link-star');
        if (starBtn.attr('data-star-enabled') !== '0') {
            starBtn.attr('data-star-enabled', '0')
                .html('<i class="iconify" data-icon="mdi:star-outline"></i> Starred');
        }
        var dt = $(this).closest('#sodar-pr-project-list').find('table').dataTable();
        var v = $(this).val();
        dt.fnFilter(v, 0); // Limit filter to title column
    });

    // Filter by starred
    $('#sodar-pr-project-list-link-star').click(function () {
        var dt = $('#sodar-pr-project-list-table').DataTable();
        $('#sodar-pr-project-list-filter').val('');
        if ($(this).attr('data-star-enabled') === '0') {
            $(this).attr('data-star-enabled', '1');
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star"></i> Starred');
        } else {
            $(this).attr('data-star-enabled', '0');
            $('#sodar-pr-project-list-link-star').html(
                '<i class="iconify" data-icon="mdi:star-outline"></i> Starred');
        }
        dt.search('').draw();
    });
});
