$(document).ready(function () {
  // Enable datatables
  $.fn.dataTable.ext.classes.sPageButton =
        'btn sodar-list-btn ml-1 sodar-paginate-button btn-outline-light ' +
        'text-primary';
  var dt = $('#sodar-pr-role-list-table').DataTable({
      ordering: true,
      order: [], // Disable default ordering
      scrollX: false,
      paging: true,
      pagingType: 'full_numbers',
      pageLength: window.roleListPagination,
      lengthChange: true,
      scrollCollapse: true,
      columnDefs: [
          {orderable: false, searchable: false, targets: [4]},
      ],  // Disable ordering and filtering for ops column
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
      dom: 'tp'
  });
  // Hide pagination if only one page
  if (dt.page.info().pages === 1) {
      $('.dataTables_paginate').hide();
  }

  // Filter input
  $('#sodar-pr-role-list-filter').keyup(function () {
      var dt = $(this).closest(
          '#sodar-pr-role-list').find('table').dataTable();
      var v = $(this).val();
      dt.fnFilter(v);
  });
});
