/* Project detail view specific JQuery */

/* Update target/peer remote project links once accessed */
let updateRemoteProjectLinks = function () {
  let linkUuids = []
  $('.sodar-pr-link-remote').each(function () {
    if (!$(this).hasClass('sodar-pr-link-remote-source') &&
      $(this).attr('disabled') === 'disabled') {
      linkUuids.push($(this).attr('data-uuid'))
    }
  })
  if (linkUuids.length > 0) {
    let queryParams = []
    for (let i = 0; i < linkUuids.length; i++) {
      queryParams.push(['rp', linkUuids[i]])
    }
    $.ajax({
      url: window.remoteLinkUrl + '?' + new URLSearchParams(queryParams),
      method: 'GET',
      dataType: 'JSON',
    }).done(function (data) {
      for (let k in data) {
        let elem = $('a[data-uuid="' + k + '"]')
        if (elem.attr('disabled') === 'disabled' && data[k] === true) {
          elem.removeAttr('disabled')
        }
      }
    })
  }
}

$(document).ready(function () {
  // Set up remote project link updating, omit categories
  if ($('div#sodar-pr-page-container-detail').attr(
      'data-project-type') === 'PROJECT') {
    updateRemoteProjectLinks()
    setInterval(function () {
      updateRemoteProjectLinks()
    }, 5000)
  }
})
