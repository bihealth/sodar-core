function makeSearchResultsCard(appIcon, cardTitle, resLength) {
  let resTitleElement = ' ' + cardTitle
  let resLengthElement = resLength ? ` (${resLength})` : ''
  let card = $('<div>', {
    class: 'card sodar-search-card'
  }).append(
    $('<div>', {
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
          }).append(
            $('<option>', {
              value: window.searchPagination,
              selected: true
            }).text('Page'),
            $('<option>', {
              value: window.searchPagination
            }).text(`${window.searchPagination} (default)`),
            $('<option>', {
              value: '10'
            }).text('10'),
            $('<option>', {
              value: '25'
            }).text('25'),
            $('<option>', {
              value: '50'
            }).text('50'),
            $('<option>', {
              value: '100'
            }).text('100'),
            $('<option>', {
              value: '-1'
            }).text('All'),
          ),
          $('<input>', {
            class: 'form-control sodar-search-filter',
            type: 'text',
            placeholder: 'Filter',
            ariaLabel: `Filter ${cardTitle}`
          }),
        ),
      ),
    ),
    // XXX: To be discussed: I found this code in the old _search_header.html template, but I can't see any other reference to result_limit. Is it still relevant?
    // {% if result_count >= result_limit %}
    //   <div class='card-body sodar-card-body-info'>
    //     <i class='iconify' data-icon='mdi:alert'></i>
    //     Some results may be omitted, please narrow down your search.
    //   </div>
    // {% endif %}
    $('<div>', {
      class: 'card-body sodar-search-card-body'
    }),
  )
  return card
}

function makeSearchResultsTable(results) {
  let table = $('<table>', {class: 'table-striped sodar-search-table'})
  let tr = $('<tr>')
  for (let field of results.field_titles) {
    tr.append($('<th>').text(field))
  }
  table.append($('<thead>').append(tr))
  let tbody = $('<tbody>')
  for (let row of results.rows) {
    let tr = $('<tr>')
    for (let field of row) {
      let td = $('<td>')
      if (field.snippets !== null) {
        for (let snippet of field.snippets) {
          $(snippet).appendTo(td)
        }
        td.append('&ensp;')
      }
      if (field.value_url !== null) {
        td.attr('class', field.cell_class)
          .append(
            $('<a>', {
              href: field.value_url,
              class: field.value_url_class
            }).text(field.value)
          )
      } else if (field.value !== null) {
        td.attr('class', field.cell_class)
          .append(field.value)
      } else {
        td.attr('class', 'text-muted')
          .append('N/A')
      }
      if (field.icons !== null) {
        td.append('&emsp;')
        for (let icon of field.icons) {
          $('<a>', {href: icon.url, title: icon.title, 'data-toggle': 'tooltip', 'data-placement': 'top'})
            .append($('<i>', {class: `iconify ${icon.class}`, 'data-icon': icon.icon}))
            .appendTo(td)
        }
      }
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
    for (let fieldIdx of highlightFields) {
      table.find(`tr td:nth-child(${fieldIdx+1})`).each(function () {
        let walker = document.createTreeWalker(this, 0x4)
        let node = walker.nextNode()
        while (node !== null) {
          $(node).replaceWith($(node).text().replaceAll(re, `<strong>$&</strong>`))
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
    let appName = $(this).data('app-name')
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
          `Error fetching search results for ${appName}: ${xhr.statusText}`
        )
      )
    }).done(data => {
      if (data['errors']) {
        console.error(data['errors'])
        $(this).html(
          $('<div>', {
            class: 'alert alert-warning',
            role: 'alert'
          })
          .text(
            `Error while searching in ${appName}: ${data['error']}`
          )
        )
        return
      }
      $(this).text('')
      for (let i = 0; i < data['results'].length; ++i) {
        let results = data['results'][i]
        let card = makeSearchResultsCard(
          $(this).data('app-icon'),
          results.title,
          results.rows.length,
        )
        $(this).append(card)
        if (!results.rows.length) {
          $(this).find('.sodar-search-card-body').html($('<p>')
            .attr('class', 'font-italic text-center m-3').text(
              'No results found.'))
          // Disable pagination and filtering for this card
          $(this).find('.sodar-search-page-length').prop(
            'disabled',
            'disabled')
          $(this).find('.sodar-search-filter').prop('disabled',
            'disabled')
          continue
        }
        let table = makeSearchResultsTable(results)
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
            .find('.sodar-search-page-length').prop('disabled',
              'disabled')
          $(table).next('.dt-paging').hide()
        }
        // Highlight search terms
        highlightSearchResults(table, results.highlight_fields, JSON.parse(searchTerms))
      }

      // Update overflow status
      modifyCellOverflow()

      /**********
       Pagination
       **********/

      $('.sodar-search-page-length').change(function () {
        let dt = $(this).closest('.sodar-search-card').find(
            'table')
          .DataTable()
        let value = parseInt($(this).val())
        dt.page.len(value).draw()
      })

      /*********
       Filtering
       *********/

      $('.sodar-search-filter').keyup(function () {
        let dt = $(this).closest('.sodar-search-card').find(
            'table')
          .dataTable().api()
        let v = $(this).val()
        dt.search(v)
        dt.draw()
      })
    })
  })
})
