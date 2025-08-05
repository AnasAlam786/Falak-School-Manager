// used in src/view/static/student.js
// used in src/view/static/promote_students.js

function sendWhatsAppMessage(phone, message) {
    // 1. Convert and validate phone
    try {
        phone = phone.toString().trim();
    } catch (e) {
        showAlert(400, "📞 Invalid phone number format.");
        return;
    }

    // 2. Remove all non-digit characters
    let formattedPhone = phone.replace(/\D/g, '');

    // 3. Handle common error cases
    if (formattedPhone.startsWith('0')) {
        formattedPhone = formattedPhone.substring(1); // remove leading 0
    }

    if (formattedPhone.length !== 10) {
        showAlert(400, "📞 Invalid phone number. It must be 10 digits.");
        return;
    }

    // 4. Add country code
    formattedPhone = '91' + formattedPhone;

    // 5. Encode the message
    const encodedMessage = encodeURIComponent(message || '');

    // 6. Check if device is mobile or desktop
    const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

    if (isMobile) {
        // Open WhatsApp on mobile
        window.location.href = `whatsapp://send?phone=${formattedPhone}&text=${encodedMessage}`;
    } else {
        // Open WhatsApp Web on desktop
        window.open(
            `https://web.whatsapp.com/send?phone=${formattedPhone}&text=${encodedMessage}`,
            '_blank'
        );
    }
}
