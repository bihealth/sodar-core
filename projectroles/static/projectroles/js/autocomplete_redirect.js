// Redirect override, adapted from Django Autocomplete Light Select2 function

document.addEventListener('dal-init-function', function () {
  yl.registerFunction('autocomplete_redirect', function ($, element) {
    let $element = $(element)

    // Templating helper
    function template(text, is_html) {
      if (is_html) {
        let $result = $('<span>')
        $result.html(text)
        return $result
      } else {
        return text
      }
    }

    function result_template(item) {
      let is_data_html = ($element.attr('data-html') !== undefined ||
        $element.attr('data-result-html') !== undefined)

      if (item['create_id']) {
        let $result = $('<span>').addClass('dal-create')
        if (is_data_html) {
          return $result.html(item.text)
        } else {
          return $result.text(item.text)
        }
      } else {
        return template(item.text, is_data_html)
      }
    }

    function selected_template(item) {
      if (item['selected_text'] !== undefined) {
        return template(item['selected_text'],
          $element.attr('data-html') !== undefined || $element.attr(
            'data-selected-html') !== undefined
        )
      } else {
        return result_template(item)
      }
    }

    let ajax = null
    if ($element.attr('data-autocomplete-light-url')) {
      ajax = {
        url: $element.attr('data-autocomplete-light-url'),
        dataType: 'json',
        delay: 250,

        data: function (params) {
          return {
            q: params.term, // search term
            page: params.page,
            create: $element.attr(
              'data-autocomplete-light-create') && !$element.attr(
              'data-tags'),
            forward: yl.getForwards($element)
          }
        },
        processResults: function (data, page) {
          if ($element.attr('data-tags')) {
            $.each(data.results, function (index, value) {
              value.id = value.text
            })
          }
          return data
        },
        cache: true
      }
    }

    $element.select2({
      tokenSeparators: $element.attr('data-tags') ? [','] : null,
      debug: true,
      containerCssClass: ':all:',
      placeholder: $element.attr('data-placeholder') || '',
      language: $element.attr('data-autocomplete-light-language'),
      minimumInputLength: $element.attr(
        'data-minimum-input-length') || 0,
      allowClear: !$element.is('[required]'),
      templateResult: result_template,
      templateSelection: selected_template,
      ajax: ajax,
      with: null,
      tags: Boolean($element.attr('data-tags')),
    })

    $element.on('select2:selecting', function (e) {
      let data = e.params.args.data
      if (data['create_id'] !== true) return
      e.preventDefault()
      let email = data.id
      let forwards = JSON.parse(yl.getForwards($element))

      $.ajax({
        url: $element.attr('data-autocomplete-light-url'),
        type: 'POST',
        dataType: 'json',
        data: {
          text: data.id,
          project: forwards.project,
          // forward: yl.getForwards($element)
        },
        beforeSend: function (xhr, settings) {
          xhr.setRequestHeader('X-CSRFToken', document
            .csrftoken)
        },
        success: function (data, textStatus, jqXHR) {
          // use hidden form to redirect to invite and send form data
          let form = document.createElement('form')
          form.setAttribute('method', 'get')
          form.setAttribute('action', data['redirect_url'])

          let hiddenMailField = document.createElement(
            'input')
          hiddenMailField.setAttribute('type', 'hidden')
          hiddenMailField.setAttribute('name', 'e')
          hiddenMailField.setAttribute('value', email)
          form.appendChild(hiddenMailField)

          let hiddenRoleField = document.createElement(
            'input')
          hiddenRoleField.setAttribute('type', 'hidden')
          hiddenRoleField.setAttribute('name', 'r')
          hiddenRoleField.setAttribute('value', forwards.role)
          form.appendChild(hiddenRoleField)

          document.body.appendChild(form)
          form.submit()
        }
      })
    })
  })
})
