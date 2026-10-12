/**
 * Main Portal JavaScript Interactions
 * Handles modals, alerts, auto-calculators, tooltips
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

  // Auto-dismiss Alerts after 6 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });

  // Number Counter Animation
  const counters = document.querySelectorAll('.counter-animate');
  counters.forEach(counter => {
    const target = +counter.getAttribute('data-target');
    if (!target) return;
    let count = 0;
    const speed = 2000 / target;

    const updateCount = () => {
      const inc = Math.max(1, Math.ceil(target / 40));
      count += inc;
      if (count < target) {
        counter.innerText = count;
        setTimeout(updateCount, 30);
      } else {
        counter.innerText = target;
      }
    };
    updateCount();
  });

  // Modal Return Book Helper
  const returnModal = document.getElementById('returnBookModal');
  if (returnModal) {
    returnModal.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const recordId = button.getAttribute('data-record-id');
      const bookTitle = button.getAttribute('data-book-title');
      const memberName = button.getAttribute('data-member-name');
      const fineAmount = button.getAttribute('data-fine-amount');
      const isOverdue = button.getAttribute('data-is-overdue') === 'true';

      const inputRecordId = returnModal.querySelector('#modal_record_id');
      const spanBookTitle = returnModal.querySelector('#modal_book_title');
      const spanMemberName = returnModal.querySelector('#modal_member_name');
      const spanFineNotice = returnModal.querySelector('#modal_fine_notice');
      const fineAmountText = returnModal.querySelector('#modal_fine_amount');

      if (inputRecordId) inputRecordId.value = recordId;
      if (spanBookTitle) spanBookTitle.textContent = bookTitle;
      if (spanMemberName) spanMemberName.textContent = memberName;

      if (spanFineNotice) {
        if (isOverdue && parseFloat(fineAmount) > 0) {
          spanFineNotice.classList.remove('d-none');
          if (fineAmountText) fineAmountText.textContent = `$${parseFloat(fineAmount).toFixed(2)}`;
        } else {
          spanFineNotice.classList.add('d-none');
        }
      }
    });
  }
});
