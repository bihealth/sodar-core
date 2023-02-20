// Set up DataTables for search tables
$(document).ready(function() {
    /*****************
     Set up DataTables
     *****************/

    $.fn.dataTable.ext.classes.sPageButton =
        'btn sodar-list-btn ml-1 sodar-paginate-button btn-outline-light text-primary';

    $('.sodar-tl-table').each(function() {
        $(this).DataTable({
            scrollX: false,
            paging: false,
            pageLength: window.searchPagination,
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
            dom: 'tp',
        });

        // Hide pagination and disable page dropdown if only one page
        if ($(this).DataTable().page.info().pages === 1) {
            $(this).closest('.sodar-sort-card')
                .find('.sodar-sort-page-length').prop('disabled', 'disabled');
            $(this).next('.dataTables_paginate').hide();
        }

        // Display card once table has been initialized
        $(this).closest('div.sodar-sort-card').show();
    });

    /*********
     Filtering
     *********/

    $('.sodar-sort-filter').keyup(function () {
        var dt = $(this).closest('.sodar-sort-card').find('table').dataTable();
        var v = $(this).val();
        dt.fnFilter(v);
    });
});
