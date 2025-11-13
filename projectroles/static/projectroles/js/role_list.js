$(document).ready(function () {
  // Enable datatables
  $.fn.dataTable.ext.classes.sPageButton =
    'btn sodar-list-btn ml-1 sodar-paginate-button btn-outline-light ' +
    'text-primary'
  let dt = $('#sodar-pr-role-list-table').DataTable({
    ordering: true,
    order: [], // Disable default ordering
    scrollX: false,
    autoWidth: false,
    paging: true,
    pagingType: 'full_numbers',
    pageLength: window.roleListPagination,
    lengthChange: true,
    scrollCollapse: true,
    columnDefs: [{
      orderable: false,
      searchable: false,
      targets: [4]
    }, ], // Disable ordering and filtering for ops column
    info: false,
    language: {paginate: sodarDataTablesPaginate},
    dom: 'tp'
  })
  // Hide pagination if only one page
  if (dt.page.info().pages === 1) {
    $('.dt-paging').hide()
  }

  // Filter input
  $('#sodar-pr-role-list-filter').keyup(function () {
    let dt = $(this).closest(
      '#sodar-pr-role-list').find('table').dataTable().api()
    let v = $(this).val()
    dt.search(v)
    dt.draw()
  })
})
