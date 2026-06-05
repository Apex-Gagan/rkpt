function getCookie(name) {
  let cookieValue = null;

  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');

    for (let i = 0; i < cookies.length; i++) {
      const cookie = $.trim(cookies[i]);

      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));

        break;
      }
    }
  }

  return cookieValue;
}

function SubmitContactForm(postUrl) {
  const csrftoken = getCookie('csrftoken');
  let submitBtn = $('#submitbtn');
  $('#submitbtn').text('Sending Your Message...');
  submitBtn.prop('disabled', true);
  const fields = {
    name_error_message: $('#name_error_message'),
    email_error_message: $('#email_error_message'),
    phone_error_message: $('#phone_error_message'),
    msg_error_message: $('#msg_error_message'),
    success_message: $('#success_message'),
    error_message: $('#error_message'),
  };

  // Reset messages
  Object.values(fields).forEach((el) => {
    el.addClass('d-none').text('');
  });

  $.ajax({
    url: postUrl,
    type: 'POST',
    data: {
      name: $('#contact-name').val().trim(),
      email: $('#contact-email').val().trim(),
      phone: $('#contact-mobile').val().trim(),
      message: $('#contact-message').val().trim(),
      csrfmiddlewaretoken: csrftoken,
    },
    success: function (response) {
      Object.keys(response).forEach((key) => {
        if (fields[key]) {
          fields[key].removeClass('d-none').text(response[key]);
        }
      });
      submitBtn.text('Message Sent Successfully!');
      $('#contact-name, #contact-email, #contact-mobile, #contact-message').val(
        ''
      );
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    },
    error: function (xhr) {
      let errors = null;

      try {
        errors = xhr.responseJSON;
      } catch (e) {}

      if (!errors) {
        fields.error_message
          .removeClass('d-none')
          .text('Something went wrong. Please try again.');
        submitBtn.prop('disabled', false);
        return;
      }

      Object.keys(errors).forEach((key) => {
        if (fields[key]) {
          fields[key].removeClass('d-none').text(errors[key]);
        }
      });
      submitBtn.text('Send Message');
    },
    complete: function () {
      submitBtn.prop('disabled', false);
      submitBtn.text('Send Message');
    },
  });
}
