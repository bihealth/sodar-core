/* Retrieve the list of users and show it as a table */

const userListCard = $('#sodar-up-user-list-card')
const userListTableBody = $('#sodar-up-user-list-table-body')
const spinner = $('#sodar-up-user-list-spinner')

$.get(userListCard.data('url')).done(data => {
  spinner.remove()
  for (let user of data) {
    const tr = $('<tr>')
    $('<td>').html(user.user_html).appendTo(tr)
    $('<td>').text(user.name).appendTo(tr)
    $('<td>').html(
      $('<a>', {
        href: 'mailto:' + user.email
      }).text(user.email)
    ).appendTo(tr)
    $('<td>').text(user.date_joined).appendTo(tr)
    userListTableBody.append(tr)
  }
  new DataTable(userListTableBody.parent('table'), {
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
    const dt = userListCard.find('table').DataTable()
    const value = parseInt($(this).val())
    dt.page.len(value).draw()
  })

  /*********
   Filtering
   *********/
  $('#sodar-up-user-list-filter').keyup(function () {
    const dt = userListCard.find('table').dataTable().api()
    const v = $(this).val()
    dt.search(v)
    dt.draw()
  })
}).catch(xhr => {
  console.error(xhr)
  userListTableBody.html(
    $('<div>', {
      class: 'alert alert-warning',
      role: 'alert'
    })
    .text(`Error fetching user list: ${xhr.statusText}`)
  )
})
