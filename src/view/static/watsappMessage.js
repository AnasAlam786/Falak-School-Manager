// used in src/view/static/student.js
// used in src/view/static/promote_students.js

function sendWhatsAppMessage(phone, message) {
    // 1. Strip non‑digits & validate
    let formattedPhone = phone.replace(/\D/g, '');
    if (formattedPhone.length !== 10) {
        showAlert(400, "📞 Invalid phone number. It must be 10 digits.");
        return;
    }
    formattedPhone = '91' + formattedPhone; // add country code

    // 2. Encode message
    const encodedMessage = encodeURIComponent(message);

    // 3. Detect mobile vs. desktop
    const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

    if (isMobile) {
        // Mobile: open WhatsApp app via custom scheme
        window.location.href =
            `whatsapp://send?phone=${formattedPhone}&text=${encodedMessage}`;
    } else {
        // Desktop: open WhatsApp Web
        window.open(
            `https://web.whatsapp.com/send?phone=${formattedPhone}&text=${encodedMessage}`,
            '_blank'
        );
    }
}