$(document).ready(function () {
  // Hide settings fields by default
  $('div[id^="div_id_settings"]').hide()
  // Hide public_access field by default
  $('#div_id_public_access').hide()
  // Hide remote sites by default
  $('div[id^="div_id_remote_site"]').hide()
  let formTitle = $('#sodar-pr-project-form-title')

  // Check if it's category/project update and show corresponding fields
  if (formTitle.attr('data-project-type') === 'PROJECT') {
    $('div[id^="div_id_settings"]').each(function () {
      let $parentDiv = $(this)
      let $projectElements = $parentDiv.find(
          '[data-project-types="project"]')
        .add($parentDiv.find('[data-project-types="project,category"]'))
      if ($projectElements.length > 0) $parentDiv.show()
      else $parentDiv.hide()
    })
    $('#div_id_public_access').show()
    $('div[id^="div_id_remote_site"]').show()
  }
  if (formTitle.attr('data-project-type') === 'CATEGORY') {
    $('div[id^="div_id_settings"]').each(function () {
      let $parentDiv = $(this)
      let $categoryElements = $parentDiv.find(
          '[data-project-types="category"]')
        .add($parentDiv.find('[data-project-types="project,category"]'))
      if ($categoryElements.length > 0) $parentDiv.show()
      else $parentDiv.hide()
    })
  }
  // Show settings fields if selected type is project/category in update form
  $('#div_id_type .form-control').change(function () {
    if ($('#div_id_type .form-control').val() === 'PROJECT') {
      $('div[id^="div_id_settings"]').each(function () {
        let $parentDiv = $(this)
        let $projectElements = $parentDiv.find(
            '[data-project-types="project"]')
          .add($parentDiv.find(
            '[data-project-types="project,category"]'))
        if ($projectElements.length > 0) $parentDiv.show()
        else $parentDiv.hide()
        $('#div_id_public_access').show()
        $('div[id^="div_id_remote_site"]').show()
      })
    } else if ($('#div_id_type .form-control').val() === 'CATEGORY') {
      $('div[id^="div_id_settings"]').each(function () {
        let $parentDiv = $(this)
        let $categoryElements = $parentDiv.find(
            '[data-project-types="category"]')
          .add($parentDiv.find(
            '[data-project-types="project,category"]'))
        if ($categoryElements.length > 0) $parentDiv.show()
        else $parentDiv.hide()
        $('#div_id_public_access').hide()
        $('div[id^="div_id_remote_site"]').hide()
      })
    }
  })

  // Warn user of revoking remote site access
  $('input[id^="id_remote_site"]').change(function () {
    if (!$(this).is(':checked') && $(this).prop('defaultChecked')) {
      const confirmMsg = 'This will revoke access to the project on ' +
        'the site. Are you sure you want to proceed?'
      if (!confirm(confirmMsg)) $(this).prop('checked', true)
      else $(this).prop('checked', false)
    }
  })
})
