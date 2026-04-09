// Set up DataTables for search tables
$(document).ready(function () {
  /*****************
   Set up DataTables
   *****************/
  $.fn.dataTable.ext.classes.sPageButton =
    'btn sodar-list-btn ml-1 sodar-paginate-button btn-outline-light text-primary'

  const form = document.querySelector("#sodar-ajax-search")
  const url = form.action
  const data = new FormData(form)
  $(".sodar-ajax-search-results").each(function() {
    let appName = $(this).data("app-name")
    $.post(url, {
      "plugin": appName,
      "terms": data.get("terms"),
      "keywords": data.get("keywords"),
    }).fail((xhr, textStatus, error) => {
      console.error(textStatus, error)
      $(this).html(
        $("<div>").attr("class", "alert alert-warning").attr("role", "alert").text(`Error fetching search results for ${appName}: ${textStatus}`)
      )
    }).done(data => {
      console.log(data)
      if (data["errors"]) {
        console.error(data["errors"])
        $(this).html(
          $("<div>").attr("class", "alert alert-warning").attr("role", "alert").text(`Error while searching in ${appName}: ${data["errors"]}`)
        )
        return
      }
      $(this).text('')
      for (let i = 0; i < data["results"].length; ++i) {
        let res = data["results"][i]
        let resTitleElement = ` ${$(this).data("app-title")}`
        let resLengthElement = res.rows.length ? ` (${res.rows.length})` : ""
        $(this).append(
          $("<div>").attr("class", "card sodar-search-card").append(
            $("<div>").attr("class", "card-header").append(
              $("<h4>").append(
                $("<i>").attr("class", "iconify").attr("data-icon", $(this).data("app-icon")),
                resTitleElement,
                resLengthElement,
                $("<div>").attr("class", "input-group sodar-header-input-group sodar-header-input-group-search pull-right").append(
                  $("<select>").attr("class", "form-control sodar-search-page-length").append(
                    $("<option>").attr("selected", true).attr("value", window.searchPagination).text("Page"),
                    $("<option>").attr("value", window.searchPagination).text(`${window.searchPagination} (default)`),
                    $("<option>").attr("value", "10").text("10"),
                    $("<option>").attr("value", "25").text("25"),
                    $("<option>").attr("value", "50").text("50"),
                    $("<option>").attr("value", "100").text("100"),
                    $("<option>").attr("value", "-1").text("All"),
                  ),
                  $("<input>", {class: "form-control sodar-search-filter", type: "text", placeholder: "Filter", ariaLabel: "Filter {{ search_title }}"}),
                )
              )
            ),
            // XXX: To be discussed: I found this code in the old _search_header.html template, but I can't see any other reference to result_limit. Is it still relevant?
            // {% if result_count >= result_limit %}
            //   <div class="card-body sodar-card-body-info">
            //     <i class="iconify" data-icon="mdi:alert"></i>
            //     Some results may be omitted, please narrow down your search.
            //   </div>
            // {% endif %}
            $("<div>").attr("class", "card-body sodar-search-card-body")
          )
        )
        if (! res.rows.length) {
          $(this).find(".sodar-search-card-body").html($("<p>").attr("class", "font-italic text-center m-3").text("No results found."))
          // Disable pagination and filtering for this card
          $(this).find('.sodar-search-page-length').prop('disabled', 'disabled')
          $(this).find('.sodar-search-filter').prop('disabled', 'disabled')
          continue
        }
        let table = $("<table>").attr("class", "table-striped sodar-search-table")
        let tr = $("<tr>")
        for (let field of res.fields) {
          tr.append($("<th>").text(field))
        }
        table.append($("<thead>").append(tr))
        let tbody = $("<tbody>")
        for (let row of res.rows) {
          let tr = $("<tr>")
          for (let j = 0; j < row.length; ++j) {
            let field = row[j]
            if (field.value_url) {
              $("<td>").attr("class", field.cell_class).append($("<a>").attr("href", field.value_url).attr("class", field.value_url_class).text(field.value)).appendTo(tr)
            } else if (field.value) {
              $("<td>").attr("class", field.cell_class).text(field.value).appendTo(tr)
            } else {
              $("<td>").attr("class", "text-muted").text("N/A").appendTo(tr)
            }
          }
          tbody.append(tr)
        }
        $(this).find(".sodar-search-card-body").append(table.append(tbody))
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
          language: {paginate: sodarDataTablesPaginate},
          dom: 'tp',
          fnDrawCallback: function () {
            modifyCellOverflow()
          }
        })
        // Hide pagination and disable page dropdown if only one page
        if ($(table).DataTable().page.info().pages === 1) {
          $(table).closest('.sodar-search-card')
            .find('.sodar-search-page-length').prop('disabled', 'disabled')
          $(table).next('.dt-paging').hide()
        }
      }

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
          .dataTable().api()
        let v = $(this).val()
        dt.search(v)
        dt.draw()
      })
    })
  })
})
