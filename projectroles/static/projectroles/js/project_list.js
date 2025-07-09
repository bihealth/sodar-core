// Function for updating custom columns
function updateCustomColumns(uuids) {
  // Grab column app names and IDs from header into a list
  let colIds = []
  $('.sodar-pr-project-list-custom-header').each(function () {
    colIds.push({
      app: $(this).attr('data-app-name'),
      id: $(this).attr('data-column-id')
    })
  })
  if (colIds.length === 0) return // Skip if no columns were found

  let getAjaxRequest = function (start, end) {
    return $.ajax({
      url: $('.sodar-pr-project-list-table').attr('data-custom-col-url'),
      method: 'POST',
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify({
        'projects': uuids.slice(start, end)
      })
    })
  }

  // Get datatables table and API
  let dt = $('#sodar-pr-project-list-table').DataTable()
  let dtApi = new $.fn.dataTable.Api('#sodar-pr-project-list-table')
  let start = 0
  let interval = 25
  let values = []
  let dfd = $.Deferred()
  let dfdNext = dfd
  dfd.resolve()

  // Populate columns with sequential queries
  while (start <= uuids.length) {
    values.push([start, start + interval])
    dfdNext.pipe(function () {
      let value = values.shift()
      return getAjaxRequest(value[0], value[1]).done(function (data) {
        $.each(data, function (uuid, projectData) {
          let dtRow = dt.row('#sodar-pr-project-list-item-' + uuid)
          let rowIdx = dtRow.index()
          let cIdx = 0
          // NOTE: We start at 1 to skip project title cell
          for (let i = 1; i < dtRow.data().length; i++) {
            let node = $(dtApi.cell(rowIdx, i).node())
            let nodeClass = node.attr('class')
            if (nodeClass &&
              nodeClass.includes('sodar-pr-project-list-custom')) {
              dtApi.cell(rowIdx, i).data(
                projectData[colIds[cIdx].app][colIds[cIdx].id]
                .html)
              cIdx += 1
            }
          }
        })
      })
    })
    start += interval
  }
}

// Function for updating role column
function updateRoleColumn(uuids) {
  let getAjaxRequest = function (start, end) {
    return $.ajax({
      url: $('.sodar-pr-project-list-table').attr('data-role-url'),
      method: 'POST',
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify({
        'projects': uuids.slice(start, end)
      })
    })
  }

  let dt = $('#sodar-pr-project-list-table').DataTable()
  let dtApi = new $.fn.dataTable.Api('#sodar-pr-project-list-table')
  let start = 0
  let interval = 25
  let values = []
  let dfd = $.Deferred()
  let dfdNext = dfd
  dfd.resolve()

  while (start <= uuids.length) {
    values.push([start, start + interval])
    dfdNext.pipe(function () {
      let value = values.shift()
      return getAjaxRequest(value[0], value[1]).done(function (data) {
        $.each(data, function (uuid, colData) {
          let dtRow = dt.row('#sodar-pr-project-list-item-' + uuid)
          let rowIdx = dtRow.index()
          let colIdx = dtRow.data().length - 1
          let node = $(dtApi.cell(rowIdx, colIdx).node())
          let nodeClass = node.attr('class')
          if (nodeClass &&
            nodeClass.includes('sodar-pr-project-list-role')) {
            dtApi.cell(rowIdx, colIdx).data(colData.name)
            if (colData.class) {
              node.attr('class', nodeClass + ' ' + colData.class)
            }
          }
        })
      })
    })
    start += interval
  }
}

// Method for toggling starred
function toggleStarring(initial) {
  let link = $('#sodar-pr-project-list-link-star')
  let dt = $('#sodar-pr-project-list-table').DataTable()
  $('#sodar-pr-project-list-filter').val('')
  if (link.attr('data-star-enabled') === '0') {
    link.attr('data-star-enabled', '1')
    $('#sodar-pr-project-list-link-star').html(
      '<i class="iconify" data-icon="mdi:star"></i> Starred')
  } else {
    link.attr('data-star-enabled', '0')
    $('#sodar-pr-project-list-link-star').html(
      '<i class="iconify" data-icon="mdi:star-outline"></i> Starred')
  }
  dt.search('').draw()
  // Set user default starring setting if no parent
  let parent = $('#sodar-pr-project-list-table').attr('data-parent')
  if (!parent && !initial) {
    $.ajax({
      url: 'project/ajax/star/home',
      method: 'POST',
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify({
        'value': link.attr('data-star-enabled')
      })
    })
  }
}

// Project list data retrieval and updating
$(document).ready(function () {
  let table = $('#sodar-pr-project-list-table')
  if (!table.length) return // Skip if project list is disabled for view

  let listUrl = table.attr('data-list-url')
  let parent = table.attr('data-parent')
  let starredDefault = table.attr('data-starred-default')
  let customColAlign = []
  $('.sodar-pr-project-list-custom-header').each(function () {
    customColAlign.push($(this).attr('data-align'))
  })
  let colCount = customColAlign.length + 2
  let allUuids = []
  let projectUuids = []
  let tableBody = $('#sodar-pr-project-list-table tbody')

  $.ajax({
    url: listUrl,
    method: 'GET',
  }).done(function (data) {
    $('#sodar-pr-project-list-loading').remove()
    // If there are no results, display message row
    if (data.projects.length === 0) {
      // let tableBody = $('#sodar-pr-project-list-table tbody')
      tableBody.append($('<tr>')
        .attr('id', 'sodar-pr-project-list-message')
        .append($('<td>')
          .attr('colspan', colCount)
          .attr('class', 'text-center text-muted font-italic')
          .text(data['messages']['no_projects'])
        )
      )
      return
    }

    // Display rows
    let projectCount = data['projects'].length
    let starredCount = 0
    const catDelim = ' / '

    for (let i = 0; i < projectCount; i++) {
      let p = data['projects'][i]
      let icon
      let projectType
      if (p['type'] === 'CATEGORY') {
        icon = 'rhombus-split'
        projectType = 'Category'
      } else {
        icon = 'cube'
        projectType = 'Project'
      }

      // Row
      tableBody.append($('<tr>')
        .attr('class',
          'sodar-pr-project-list-item sodar-pr-project-list-item-' +
          p['type'].toLowerCase())
        .attr('id', 'sodar-pr-project-list-item-' + p['uuid'])
        .attr('data-uuid', p['uuid'])
        .attr('data-full-title', p['full_title'])
        .attr('data-starred', +p['starred'])
      )
      if (p['starred']) starredCount += 1
      let row = tableBody.find('tr:last')

      // Title column
      let tElem = '<a>'
      let tHref = '/project/' + p['uuid']
      let tClass = 'sodar-pr-project-link'
      if (!p['access']) {
        tElem = '<span>'
        tHref = ''
        tClass = 'text-muted sodar-pr-project-link-disabled'
      }
      // Highlight project title in category structure
      let titleHtml = ''
      if (data['user']['highlight'] &&
        projectType.toUpperCase() === 'PROJECT' &&
        (parent || p['full_title'].includes(catDelim))) {
        let titleSplit = p['full_title'].split(catDelim)
        let splitLen = titleSplit.length
        titleHtml = titleSplit.slice(0, splitLen - 1).join(catDelim)
        if (titleHtml.length) titleHtml += catDelim
        titleHtml += '<strong>' + titleSplit[splitLen - 1] + '</strong>'
      } else titleHtml = p['full_title']
      row.append($('<td>')
        .attr('class', 'sodar-pr-project-list-title-td')
        .append($('<div>')
          .attr('class', 'sodar-pr-project-title-container')
          .append($('<i>')
            .attr('class', 'iconify mr-1')
            .attr('data-icon', 'mdi:' + icon)
            .attr('title', projectType)
          )
          .append($('<span>')
            .attr('class', 'sodar-pr-project-title')
            .append($(tElem)
              .attr('class', tClass)
              .attr('href', tHref)
              .html(titleHtml)
            )
          )
        )
      )

      // Add icons to title columns
      let titleSpan = row.find($('span.sodar-pr-project-title'))
      // Remote icon
      if (p['remote']) {
        let textClass
        if (p['revoked']) textClass = 'text-danger'
        else textClass = 'text-info'
        titleSpan.append($('<i>')
          .attr('class',
            'iconify text-info ml-1 sodar-pr-remote-project-icon ' +
            textClass)
          .attr('data-icon', 'mdi:cloud')
          .attr('title', 'Remote synchronized from source site')
        )
      }
      // Public icon
      if (p['type'] === 'PROJECT' && p['public_access']) {
        titleSpan.append($('<i>')
          .attr('class',
            'iconify text-info ml-1 sodar-pr-project-public')
          .attr('data-icon', 'mdi:earth')
          .attr('title', 'Public read-only access')
        )
      } else if (p['type'] === 'CATEGORY' && p['public_stats']) {
        titleSpan.append($('<i>')
          .attr('class',
            'iconify text-info ml-1 sodar-pr-project-stats')
          .attr('data-icon', 'mdi:chart-box')
          .attr('title', 'Public statistics displayed')
        )
      }
      // Archived icon
      if (p['type'] === 'PROJECT' && p['archive']) {
        titleSpan.append($('<i>')
          .attr('class',
            'iconify text-info ml-1 sodar-pr-project-archive')
          .attr('data-icon', 'mdi:archive')
          .attr('title', 'Archived')
        )
      }
      // Starred icon
      if (p['starred']) {
        titleSpan.append($('<i>')
          .attr('class',
            'iconify text-warning ml-1 sodar-pr-project-starred')
          .attr('data-icon', 'mdi:star')
        )
      }
      // Blocked icon
      if (p['blocked']) {
        titleSpan.append($('<i>')
          .attr('class',
            'iconify text-danger ml-1 sodar-pr-project-blocked')
          .attr('data-icon', 'mdi:cancel')
          .attr('title',
            'Access temporarily blocked by administrators')
        )
      }
      // Finder link
      if (!p['blocked'] && !p['access'] && p['finder_url']) {
        titleSpan.append($('<a>')
          .attr('href', p['finder_url'])
          .attr('class', 'sodar-pr-project-findable')
          .attr('title', 'Findable project: Request access from ' +
            'category owner or delegate')
          .append($('<i>')
            .attr('class', 'iconify ml-1')
            .attr('data-icon', 'mdi:account-supervisor')

          )
        )
      }

      // Fill project custom columns with spinners
      for (let j = 1; j < colCount - 1; j++) {
        if (p['type'] === 'PROJECT' && p['access']) {
          row.append($('<td>')
            .attr('class',
              'sodar-pr-project-list-custom text-' +
              customColAlign[j - 1])
            .append($('<i>')
              .attr('class', 'iconify spin text-muted ' +
                'sodar-pr-project-list-load-icon')
              .attr('data-icon', 'mdi:loading')
            )
          )
        } else row.append($('<td>'))
      }
      // Add user role column
      if (!data['user']['superuser'] && p['access']) {
        row.append($('<td>')
          .attr('class', 'sodar-pr-project-list-role')
          .append($('<i>')
            .attr('class', 'iconify spin text-muted ' +
              'sodar-pr-project-list-load-icon')
            .attr('data-icon', 'mdi:loading')
          )
        )
      } else if (!data['user']['superuser']) {
        row.append($('<td>')
          .attr('class', 'sodar-pr-project-list-role text-muted')
          .html('N/A')
        )
      }

      // Add categories and projects with access for further queries
      if (p['access']) {
        allUuids.push(p['uuid'])
        if (p['type'] === 'PROJECT') {
          projectUuids.push(p['uuid'])
        }
      }
    }

    // Enable starred button and filter
    let starringEnabled = false
    if (starredCount > 0 && starredCount < projectCount) {
      $('#sodar-pr-project-list-link-star').prop('disabled', false)
      starringEnabled = true
    }
    if (projectCount > 1) {
      $('#sodar-pr-project-list-filter').prop('disabled', false)
    }

    // Enable datatables
    $.fn.dataTable.ext.classes.sPageButton =
      'btn sodar-list-btn ml-1 sodar-paginate-button btn-outline-light ' +
      'text-primary'
    let dt = $('#sodar-pr-project-list-table').DataTable({
      ordering: false,
      scrollX: false,
      paging: true,
      pagingType: 'full_numbers',
      pageLength: window.projectListPagination,
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
      dom: 'tp'
    })
    // Hide pagination if only one page
    if (dt.page.info().pages === 1) {
      // TODO: Disable pagination control once implemented
      $('.dataTables_paginate').hide()
    }
    // Add star filter
    $.fn.dataTable.ext.search.push(
      function (settings, data, dataIndex, rowObj, counter) {
        let api = new $.fn.dataTable.Api(
          '#sodar-pr-project-list-table')
        let filterEnabled = $('#sodar-pr-project-list-link-star')
          .attr('data-star-enabled')
        if (filterEnabled === '1') {
          return $(api.row(dataIndex).node()).data('starred')
        } else return true
      })
    // Handle page length change
    $('#sodar-pr-project-list-page-length').change(function () {
      let dt = $(this).closest(
        '#sodar-pr-project-list').find('table').DataTable()
      let value = parseInt($(this).val())
      dt.page.len(value).draw()
      // Update user setting
      $.ajax({
        url: 'project/api/settings/set/user',
        method: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
          'plugin_name': 'projectroles',
          'setting_name': 'project_list_pagination',
          'value': value
        })
      })
    })

    // Toggle star filter
    if (starredDefault === '1' && starringEnabled) {
      toggleStarring(true)
    }

    if (projectUuids.length > 0) {
      // Update custom columns
      updateCustomColumns(projectUuids)
    }
    if (allUuids.length > 0) {
      // Update role column
      if (!data['user']['superuser']) {
        updateRoleColumn(allUuids)
      }
    }
  })

  // Filter input
  $('#sodar-pr-project-list-filter').keyup(function () {
    let starBtn = $('#sodar-pr-project-list-link-star')
    if (starBtn.attr('data-star-enabled') !== '0') {
      starBtn.attr('data-star-enabled', '0')
        .html(
          '<i class="iconify" data-icon="mdi:star-outline"></i> Starred'
        )
    }
    let dt = $(this).closest(
      '#sodar-pr-project-list').find('table').dataTable()
    let v = $(this).val()
    dt.fnFilter(v, 0) // Limit filter to title column
  })

  // Filter by starred
  $('#sodar-pr-project-list-link-star').click(function () {
    // Clear filter and toggle starring
    $('#sodar-pr-project-list-link-star').value = ''
    let dt = $(this).closest(
      '#sodar-pr-project-list').find('table').dataTable()
    dt.fnFilter('', 0)
    toggleStarring(false)
  })
})
