/* Retrieve the list of users and show it as a table */

const userList = $('#sodar-up-ajax-user-list')
const userListTable = $('#sodar-up-ajax-user-list-table')
const spinner = $('#sodar-up-user-list-spinner')

$.get(userList.data('url')).done(data => {
  spinner.remove()
  for (let user of data) {
    tr = $('<tr>')
    $('<td>').html(
      $('<a>', {
        href: userList.data('link-prefix') + '/' + user.sodar_uuid
      }).text(user.username)
    ).appendTo(tr)
    $('<td>').text(user.first_name).appendTo(tr)
    $('<td>').text(user.last_name).appendTo(tr)
    $('<td>').html(
      $('<a>', {
        href: 'mailto:' + user.email
      }).text(user.email)
    ).appendTo(tr)
    $('<td>').text(user.is_active).appendTo(tr)
    $('<td>').text(user.date_joined).appendTo(tr)
    $('<td>').html($('<code>').text(user.sodar_uuid)).appendTo(tr)
    userListTable.append(tr)
  }
  new DataTable(userListTable.parent('table'), {
    order: [], // Disable default ordering
    scrollX: false,
    autoWidth: false,
    paging: true,
    pagingType: 'full_numbers',
    pageLength: 10,
    lengthChange: true,
    scrollCollapse: true,
    info: false,
    language: {
      paginate: sodarDataTablesPaginate
    },
    dom: 'tp',
  })

  /**********
   Pagination
   **********/
  $('#sodar-up-user-list-page-length').change(function () {
    const dt = userList.find('table').DataTable()
    const value = parseInt($(this).val())
    dt.page.len(value).draw()
  })

  /*********
   Filtering
   *********/
  $('#sodar-up-user-list-filter').keyup(function () {
    const dt = userList.find('table').dataTable().api()
    const v = $(this).val()
    dt.search(v)
    dt.draw()
  })
}).catch(xhr => {
  console.error(xhr)
  userListTable.html(
    $('<div>', {
      class: 'alert alert-warning',
      role: 'alert'
    })
    .text(
      `Error fetching user list: ${xhr.statusText}`
    )
  )
})
