$(document).ready(function () {
  $('.martor-preview').each(function () {
    let target = this
    $(target).addClass('sodar-markdown-content')
    let martorPreviewObserver = new MutationObserver(function () {
      if ($(target).hasClass('martor-preview-stale')) {
        this.disconnect()
        $(target).text('Markdown preview')
        this.observe(target, {
          childList: true,
        })
      }
    })
    martorPreviewObserver.observe(this, {
      childList: true,
    })
  })
})
