function makeSearchResultsCard(appIcon, cardTitle, resLength, resLimit) {
  const resTitleElement = ' ' + cardTitle
  const resLengthElement = resLength ? ` (${resLength})` : ''
  const paginationOptions = [
    {value: window.searchPagination, label: 'Page', selected: true},
    {value: window.searchPagination, label: `${window.searchPagination} (default)`},
    {value: 10, label: '10'},
    {value: 25, label: '25'},
    {value: 50, label: '50'},
    {value: 100, label: '100'},
    {value: -1, label: 'All'},
  ]
  const card = $('<div>', {
    class: 'card sodar-search-card'
  })
  const cardHeader = $('<div>', {
    class: 'card-header'
  }).append(
    $('<h4>').append(
      $('<i>', {
        class: 'iconify',
        'data-icon': appIcon
      }),
      resTitleElement,
      resLengthElement,
      $('<div>', {
        class: 'input-group sodar-header-input-group sodar-header-input-group-search pull-right'
      }).append(
        $('<select>', {
          class: 'form-control sodar-search-page-length'
        }).append(paginationOptions.map(x => $('<option>', x))),
        $('<input>', {
          class: 'form-control sodar-search-filter',
          type: 'text',
          placeholder: 'Filter',
          ariaLabel: `Filter ${cardTitle}`
        }),
      ),
    ),
  )
  card.append(cardHeader)
  if (resLimit >= 0 && resLength >= resLimit) {
    const cardResultLimitWarning = $('<div>', {
      class: 'card-body sodar-card-body-info'
    }).append(
      $('<i>', {
        class: 'iconify',
        'data-icon': 'mdi:alert',
      }),
      'Some results may be omitted, please narrow down your search.',
    )
    card.append(cardResultLimitWarning)
  }
  const cardBody = $('<div>', {
    class: 'card-body sodar-search-card-body'
  })
  card.append(cardBody)
  return card
}

function makeSearchResultsTable(result) {
  const table = $('<table>', {
    class: `table table-striped sodar-card-table sodar-search-table ${result.table_class}`
  })
  const tr = $('<tr>')
  for (let column of result.columns) {
    tr.append($('<th>').text(column.title))
  }
  table.append($('<thead>').append(tr))
  const tbody = $('<tbody>')
  for (let row of result.rows) {
    const tr = $('<tr>')
    for (let fieldIdx in row) {
      const column = result.columns[fieldIdx]
      const cell = row[fieldIdx]
      const cellDiv = $('<div>')
      if (column.value_html == true) {
        cellDiv.append(cell.value)
      } else if (cell.value_url !== null) {
        cellDiv.append(
            $('<a>', {
              href: cell.value_url,
            }).text(cell.value)
          )
      } else if (cell.value !== null) {
        cellDiv.append(cell.value)
      } else {
        cellDiv.addClass('text-muted')
        cellDiv.append('N/A')
      }
      const td = $('<td>')
      if (column.column_class !== null) {
        td.addClass(column.column_class)
      }
      if (cell.cell_class !== null) {
        td.addClass(cell.cell_class)
      }
      td.append(cellDiv)
      tr.append(td)
    }
    tbody.append(tr)
  }
  table.append(tbody)
  return table
}

function highlightSearchResults(table, highlightFields, searchTerms) {
  for (let term of searchTerms) {
    const re = new RegExp(term, 'ig')
    for (let fieldIdx in highlightFields) {
      table.find(`tr td:nth-child(${fieldIdx+1})`).each(function () {
        const walker = document.createTreeWalker(this, 0x4)
        let node = walker.nextNode()
        while (node !== null) {
          $(node).replaceWith($(node).text().replaceAll(re,
            `<strong>$&</strong>`))
          node = walker.nextNode()
        }
      })
    }
  }
}

// Set up DataTables for search tables
$(document).ready(function () {
  /*****************
   Set up DataTables
   *****************/
  $.fn.dataTable.ext.classes.sPageButton =
    'btn sodar-list-btn ml-1 sodar-paginate-button btn-outline-light text-primary'

  const form = document.querySelector('#sodar-ajax-search')
  const url = form.action
  const data = new FormData(form)
  const searchTerms = data.get('terms')
  $('.sodar-ajax-search-results').each(function () {
    const appName = $(this).data('app-name')
    $.post(url, {
      'plugin': appName,
      'terms': searchTerms,
      'keywords': data.get('keywords'),
    }).fail((xhr, textStatus, error) => {
      console.error(xhr.status, textStatus, error)
      $(this).html(
        $('<div>', {
          class: 'alert alert-warning',
          role: 'alert'
        })
        .text(
          `Error fetching search results for the ${appName} app: ${xhr.statusText}`
        )
      )
    }).done(data => {
      if (data['error']) {
        console.error(data['error'])
        $(this).html(
          $('<div>', {
            class: 'alert alert-warning',
            role: 'alert'
          })
          .text(
            `Error while searching in the ${appName} app: ${data['error']}`
          )
        )
        return
      }
      $(this).text('')
      for (let i = 0; i < data['results'].length; ++i) {
        const results = data['results'][i]
        const card = makeSearchResultsCard(
          $(this).data('app-icon'),
          results.title,
          results.rows.length,
          results.result_limit,
        )
        $(this).append(card)
        if (!results.rows.length) {
          $(this).find('.sodar-search-card-body').html(
            $('<p>').attr('class', 'font-italic text-center m-3')
            .text('No results found.')
          )
          // Disable pagination and filtering for this card
          $(this).find('.sodar-search-page-length').prop('disabled',
            'disabled')
          $(this).find('.sodar-search-filter').prop('disabled',
            'disabled')
          continue
        }
        const table = makeSearchResultsTable(results)
        $(this).find('.sodar-search-card-body').append(table)
        $(table).DataTable({
          order: [], // Disable default ordering
          scrollX: false,
          autoWidth: false,
          paging: true,
          pagingType: 'full_numbers',
          pageLength: window.searchPagination,
          lengthChange: true,
          scrollCollapse: true,
          info: false,
          language: {
            paginate: sodarDataTablesPaginate
          },
          dom: 'tp',
          fnDrawCallback: function () {
            modifyCellOverflow()
          }
        })
        // Hide pagination and disable page dropdown if only one page
        if ($(table).DataTable().page.info().pages === 1) {
          $(table).closest('.sodar-search-card')
            .find('.sodar-search-page-length')
            .prop('disabled', 'disabled')
          $(table).next('.dt-paging').hide()
        }
        // Highlight search terms
        highlightSearchResults(
          table,
          results.highlight_fields,
          JSON.parse(searchTerms),
        )
      }

      // Update overflow status
      modifyCellOverflow()

      /**********
       Pagination
       **********/

      $('.sodar-search-page-length').change(function () {
        const dt = $(this).closest('.sodar-search-card').find(
            'table')
          .DataTable()
        const value = parseInt($(this).val())
        dt.page.len(value).draw()
      })

      /*********
       Filtering
       *********/

      $('.sodar-search-filter').keyup(function () {
        const dt = $(this).closest('.sodar-search-card').find(
            'table')
          .dataTable().api()
        const v = $(this).val()
        dt.search(v)
        dt.draw()
      })
    })
  })
})
