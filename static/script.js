document.addEventListener("DOMContentLoaded", () => {
    const texts = [
      "Revolutionizing Waste Management",
      "AI-Powered Smart Segregation",
      "Eco-Friendly Automation Engine"
    ];
    const element = document.getElementById("typewriter");
  
    let i = 0;
    let charIndex = 0;
    let isDeleting = false;
    let currentText = "";
    let currentPhraseIndex = 0;
  
    function typeWriter() {
      const fullText = texts[currentPhraseIndex];
  
      if (!isDeleting) {
        if (charIndex < fullText.length) {
          const span = document.createElement("span");
          const char = fullText.charAt(charIndex);
          span.innerHTML = char;
          element.appendChild(span);
          currentText += char;
          charIndex++;
          setTimeout(typeWriter, 80);
        } else {
          isDeleting = true;
          setTimeout(typeWriter, 1500);
        }
      } else {
        if (charIndex > 0) {
          element.innerHTML = currentText.slice(0, -1);
          currentText = currentText.slice(0, -1);
          charIndex--;
          setTimeout(typeWriter, 40);
        } else {
          isDeleting = false;
          currentPhraseIndex = (currentPhraseIndex + 1) % texts.length;
          setTimeout(typeWriter, 1000);
        }
      }
    }
  
    typeWriter();
  });
  

// Upload Prediction Logic
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const formData = new FormData();
  formData.append('file', document.getElementById('file').files[0]);

  const response = await fetch('/predict', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  document.getElementById('result').innerText = `Prediction: ${result.prediction}\n${result.disposal_instructions}`;
});

document.getElementById('file').addEventListener('change', function () {
  const preview = document.getElementById('preview');
  const container = document.getElementById('preview-container');
  const file = this.files[0];

  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      preview.src = e.target.result;
      container.style.display = 'block';
    };
    reader.readAsDataURL(file);
  } else {
    container.style.display = 'none';
  }
});
function toggleSignInModal() {
    const modal = document.getElementById("signin-modal");
    modal.style.display = modal.style.display === "flex" ? "none" : "flex";
  }
  