function makeSearchResultCardHeader(appIcon, cardTitle, resLength) {
  const resTitleElement = ' ' + cardTitle
  const resLengthElement = resLength ? ` (${resLength})` : ''
  const paginationOptions = [{
    value: window.searchPagination,
    label: 'Page',
    selected: true
  }, {
    value: window.searchPagination,
    label: `${window.searchPagination} (default)`
  }, {
    value: 10,
    label: '10'
  }, {
    value: 25,
    label: '25'
  }, {
    value: 50,
    label: '50'
  }, {
    value: 100,
    label: '100'
  }, {
    value: -1,
    label: 'All'
  }]
  return $('<div>', {
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
}

function makeSearchResultsCard(appIcon, cardTitle, resLength, resLimit) {
  const card = $('<div>', {
    class: 'card sodar-search-card'
  })
  cardHeader = makeSearchResultCardHeader(appIcon, cardTitle, resLength)
  card.append(cardHeader)
  if (resLimit > 0 && resLength >= resLimit) {
    const cardResultLimitWarning = $('<div>', {
      class: 'card-body sodar-card-body-info'
    }).append(
      $('<i>', {
        class: 'iconify',
        'data-icon': 'mdi:alert',
      }),
      ' Some results may be omitted, please narrow down your search.',
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
    class: 'table table-striped sodar-card-table sodar-search-table',
  })
  if (result.table_class) {
    table.addClass(result.table_class)
  }
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
      if (column.overflow) {
        cellDiv.addClass('sodar-overflow-container')
      }
      if (column.value_html) {
        cellDiv.append(cell.value)
      } else if (cell.value_url) {
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
      if (column.column_class) {
        td.addClass(column.column_class)
      }
      if (cell.cell_class) {
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

function renderSearchResults(parentContainer, result, searchTerms) {
  const card = makeSearchResultsCard(
    parentContainer.data('app-icon'),
    result.title,
    result.rows.length,
    result.result_limit,
  )
  parentContainer.append(card)
  cardBody = card.find('.sodar-search-card-body')
  if (!result.rows.length) {
    const emptyTable = $('<table>', {
      class: 'table table-striped sodar-card-table',
    })
    if (result.table_class) {
      emptyTable.addClass(result.table_class)
    }
    // Append an empty table to simplify UI unit tests
    cardBody.append(
      emptyTable,
      $('<p>').attr('class',
        'sodar-search-not-found-alert font-italic text-center m-3')
      .text('No results found.')
    )
    // Disable pagination and filtering for this card
    card.find('.sodar-search-page-length').prop('disabled',
      'disabled')
    card.find('.sodar-search-filter').prop('disabled',
      'disabled')
    return
  }
  const table = makeSearchResultsTable(result)
  cardBody.append(table)

  /************************
   DataTable Initialization
   ************************/

  unorderableColumns = []
  unsearchableColumns = []
  for (let i = 0; i < result.columns.length; ++i) {
    const column = result.columns[i]
    if (!column.orderable) {
      unorderableColumns.push(i)
    }
    if (!column.searchable) {
      unsearchableColumns.push(i)
    }
  }
  console.log(unorderableColumns)
  const tableDT = $(table).DataTable({
    order: [], // Disable default ordering
    scrollX: false,
    autoWidth: false,
    paging: true,
    pagingType: 'full_numbers',
    pageLength: window.searchPagination,
    lengthChange: true,
    scrollCollapse: true,
    columnDefs: [{
      orderable: false,
      targets: unorderableColumns,
    }, {
      searchable: false,
      targets: unsearchableColumns,
    }, ],
    info: false,
    language: {
      paginate: sodarDataTablesPaginate
    },
    dom: 'tp',
  })

  /*********************
   Cosmetic Improvements
   *********************/

  // Overflow status
  modifyCellOverflow()
  // Hide pagination and disable page dropdown if only one page
  if (tableDT.page.info().pages === 1) {
    card.find('.sodar-search-page-length').prop('disabled', 'disabled')
    $(table).next('.dt-paging').hide()
  }
  // Highlight search terms
  highlightSearchResults(
    table,
    result.columns,
    JSON.parse(searchTerms),
  )
}

function highlightSearchResults(table, columns, searchTerms) {
  const re = new RegExp(searchTerms.join('|'), 'ig')
  for (let fieldIdx in columns) {
    if (columns[fieldIdx].highlight == true) {
      table.find(`tr td:nth-child(${fieldIdx+1})`).each(function () {
        const walker = document.createTreeWalker(this, 0x4)
        let node = walker.nextNode()
        while (node !== null) {
          $(node).replaceWith($(node).text().replaceAll(re,
            `<strong class="sodar-search-highlight">$&</strong>`))
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

  const resultCalls = $('.sodar-ajax-search-results').map(function () {
    const url = $(this).data('url')
    const appName = $(this).data('app-name')
    const searchTerms = document.getElementById('search-terms').textContent
    const searchKeywords = document.getElementById('search-keywords').textContent
    return $.post(url, {
      'plugin': appName,
      'terms': searchTerms,
      'keywords': searchKeywords,
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
      for (let result of data['results']) {
        renderSearchResults($(this), result, searchTerms)
      }
    }).catch(xhr => {
      $(this).html(
        $('<div>', {
          class: 'alert alert-warning',
          role: 'alert'
        })
        .text(
          `Error fetching search results for the ${appName} app: ${xhr.statusText}`
        )
      )
    })
  })

  $.when.apply($, resultCalls).done(() => {
    $(document).trigger('searchResultsLoaded')
    $('#sodar-search-results-spinner').text('')

    /**********
     Pagination
     **********/

    $('.sodar-search-page-length').change(function () {
      const dt = $(this).closest('.sodar-search-card')
        .find('table')
        .DataTable()
      const value = parseInt($(this).val())
      dt.page.len(value).draw()
    })

    /*********
     Filtering
     *********/

    $('.sodar-search-filter').keyup(function () {
      const dt = $(this).closest('.sodar-search-card')
        .find('table')
        .dataTable()
        .api()
      const v = $(this).val()
      dt.search(v)
      dt.draw()
    })
  })
})
