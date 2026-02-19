$(document).ready(function () {
  console.log('ready')
  $('.martor-preview').each(function() {
    console.log($(this))
    $(this).addClass('sodar-markdown-content')
  })
})
