// Set up DataTables for search tables
$(document).ready(function () {
  /*****************
   Set up DataTables
   *****************/

  $.fn.dataTable.ext.classes.sPageButton =
    'btn sodar-list-btn ml-1 sodar-paginate-button btn-outline-light text-primary'

  $('.sodar-search-table').each(function () {
    $(this).DataTable({
      order: [], // Disable default ordering
      scrollX: false,
      paging: true,
      pagingType: 'full_numbers',
      pageLength: window.searchPagination,
      lengthChange: true,
      scrollCollapse: true,
      info: false,
      language: {
        paginate: {
          first: '<i class="iconify text-primary" ' +
            'data-icon="mdi:arrow-left-circle-outline"></i> First',
          previous: '<i class="iconify text-primary" ' +
            'data-icon="mdi:arrow-left-circle"></i> Prev',
          next: 'Next <i class="iconify text-primary" ' +
            'data-icon="mdi:arrow-right-circle"></i>',
          last: 'Last <i class="iconify text-primary" ' +
            'data-icon="mdi:arrow-right-circle-outline"></i>',
        }
      },
      dom: 'tp',
      fnDrawCallback: function () {
        modifyCellOverflow()
      }
    })

    // Hide pagination and disable page dropdown if only one page
    if ($(this).DataTable().page.info().pages === 1) {
      $(this).closest('.sodar-search-card')
        .find('.sodar-search-page-length').prop('disabled', 'disabled')
      $(this).next('.dataTables_paginate').hide()
    }

    // Display card once table has been initialized
    $(this).closest('div.sodar-search-card').show()
  })

  // Display not found once all DataTables have been initialized
  $('div#sodar-search-not-found-alert').removeClass('d-none')

  // Update overflow status
  modifyCellOverflow()

  /**********
   Pagination
   **********/

  $('.sodar-search-page-length').change(function () {
    let dt = $(this).closest('.sodar-search-card').find('table')
      .DataTable()
    let value = parseInt($(this).val())
    dt.page.len(value).draw()
  })

  /*********
   Filtering
   *********/

  $('.sodar-search-filter').keyup(function () {
    let dt = $(this).closest('.sodar-search-card').find('table')
      .dataTable()
    let v = $(this).val()
    dt.fnFilter(v)
  })
})
