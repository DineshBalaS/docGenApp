document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("docgen-form");
  const previewBtn = document.getElementById("preview-btn");
  const previewSection = document.getElementById("preview-section");
  const previewBox = document.getElementById("preview");

  if (previewBtn && form && previewSection && previewBox) {
    previewBtn.addEventListener("click", () => {
      const formData = new FormData(form);
      let html =
        "<h2 class='text-lg font-bold mb-4'>Preview Summary</h2><ul class='list-disc ml-6 space-y-1'>";

      formData.forEach((value, key) => {
        html += `<li><strong>${key}:</strong> ${value}</li>`;
      });
      html += "</ul>";

      previewBox.innerHTML = html;
      previewSection.classList.remove("hidden");
    });
  }
});
