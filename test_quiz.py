<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ quiz.title }} — منصة الاختبارات</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Tajawal', sans-serif; }
  </style>
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen pb-16">

  <!-- شريط الرأس والعداد التنازلي الثابت -->
  <header class="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200 shadow-sm px-4 py-3">
    <div class="max-w-3xl mx-auto flex items-center justify-between">
      <div>
        <h1 class="font-bold text-slate-900 text-sm md:text-base leading-tight">{{ quiz.title }}</h1>
        <p class="text-xs text-slate-500">{{ user.name }} | الشعبة {{ user.class_name }}</p>
      </div>
      <div class="flex items-center gap-2 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-xl">
        <span class="text-xs text-amber-700 font-medium">الوقت المتبقي:</span>
        <span id="timerDisplay" class="font-mono font-bold text-amber-800 text-base md:text-lg">20:00</span>
      </div>
    </div>
  </header>

  <main class="max-w-3xl mx-auto px-4 pt-6">

    <!-- تنبيه نظام العلامات السالبة -->
    {% if quiz.has_negative_marking %}
    <div class="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-3">
      <span class="text-xl">⚠️</span>
      <div class="text-xs md:text-sm leading-relaxed">
        <strong>تنبيه علامات سالبة:</strong> يخصم <strong>({{ quiz.negative_mark_value }})</strong> نقطة عن كل إجابة خاطئة. 
        <span class="block mt-0.5 text-amber-700">الأسئلة المتروكة فارغة لا تخصم نقاطاً. يمكنك مسح إجابتك أو النقر عليها مجدداً لإلغائها.</span>
      </div>
    </div>
    {% endif %}

    <!-- نموذج الاختبار -->
    <form id="quizForm" method="POST" action="/quiz/{{ quiz.id }}/submit" onsubmit="return handleFormSubmit(event)">
      
      <div class="space-y-6">
        {% for q in questions %}
        <div class="bg-white border border-slate-200 rounded-2xl p-5 md:p-6 shadow-sm">
          
          <!-- رأس السؤال مع زر إلغاء الاختيار -->
          <div class="flex items-center justify-between gap-2 mb-3 pb-2 border-b border-slate-100">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-lg">السؤال {{ loop.index }} من {{ questions|length }}</span>
              <span class="text-xs font-medium text-slate-400">{{ q.points }} نقطة</span>
            </div>
            
            <!-- زر مسح الاختيار لتجنب العلامة السالبة -->
            <button type="button" onclick="clearAnswer('q_{{ q.id }}')" class="text-xs text-rose-500 hover:text-rose-700 hover:bg-rose-50 font-bold px-2 py-1 rounded-lg transition cursor-pointer">
              إلغاء الاختيار ✕
            </button>
          </div>

          <p class="text-base md:text-lg font-bold text-slate-900 mb-4 leading-relaxed">{{ q.question_text }}</p>

          <div class="space-y-2.5">
            {% for opt_key, opt_text in [('A', q.option_a), ('B', q.option_b), ('C', q.option_c), ('D', q.option_d)] %}
            <label class="flex items-center gap-3 p-3.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition select-none has-[:checked]:border-indigo-600 has-[:checked]:bg-indigo-50/50">
              <input type="radio" name="q_{{ q.id }}" value="{{ opt_key }}" class="w-4 h-4 text-indigo-600 border-slate-300 focus:ring-indigo-500">
              <span class="text-sm md:text-base text-slate-700 font-medium">{{ opt_text }}</span>
            </label>
            {% endfor %}
          </div>
        </div>
        {% endfor %}
      </div>

      <!-- زر تسليم الاختبار -->
      <div class="mt-8 pt-4 border-t border-slate-200">
        <button type="submit" id="submitBtn" class="w-full py-4 bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] text-white font-bold text-base rounded-2xl shadow-lg shadow-emerald-600/20 transition cursor-pointer">
          تسليم الإجابات وإنهاء الاختبار
        </button>
      </div>

    </form>
  </main>

  <script>
    // --- 1. ميزة إلغاء التحديد بالنقر المزدوج أو بالزر ---
    function clearAnswer(radioName) {
      const radios = document.querySelectorAll(`input[name="${radioName}"]`);
      radios.forEach(r => {
        r.checked = false;
        r.dataset.wasChecked = "false";
      });
    }

    // السماح بإلغاء التحديد بالنقر على نفس الخيار مجدداً
    document.querySelectorAll('input[type="radio"]').forEach(radio => {
      radio.addEventListener('click', function() {
        if (this.dataset.wasChecked === "true") {
          this.checked = false;
          this.dataset.wasChecked = "false";
        } else {
          document.querySelectorAll(`input[name="${this.name}"]`).forEach(r => r.dataset.wasChecked = "false");
          this.dataset.wasChecked = "true";
        }
      });
    });

    // --- 2. إدارة العداد التنازلي والتسليم التلقائي ---
    const durationMinutes = {{ quiz.duration_minutes or 20 }};
    let remainingSeconds = durationMinutes * 60;
    let isAutoSubmitting = false;

    const timerDisplay = document.getElementById("timerDisplay");
    const quizForm = document.getElementById("quizForm");

    const timerInterval = setInterval(() => {
      remainingSeconds--;
      
      const mins = Math.floor(remainingSeconds / 60);
      const secs = remainingSeconds % 60;
      timerDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

      if (remainingSeconds <= 120) {
        timerDisplay.parentElement.classList.remove('bg-amber-50', 'border-amber-200');
        timerDisplay.parentElement.classList.add('bg-rose-50', 'border-rose-200');
        timerDisplay.classList.remove('text-amber-800');
        timerDisplay.classList.add('text-rose-700', 'animate-pulse');
      }

      if (remainingSeconds <= 0) {
        clearInterval(timerInterval);
        isAutoSubmitting = true;
        alert("انتهى الوقت المحدد للاختبار! سيتم تسليم إجاباتك الحالية تلقائياً.");
        quizForm.submit();
      }
    }, 1000);

    // --- 3. التحقق من الأسئلة الفارغة وتأكيد التسليم ---
    function handleFormSubmit(e) {
      if (isAutoSubmitting) return true;

      const totalQuestions = {{ questions|length }};
      let answeredCount = 0;

      {% for q in questions %}
      if (document.querySelector('input[name="q_{{ q.id }}"]:checked')) {
        answeredCount++;
      }
      {% endfor %}

      const unansweredCount = totalQuestions - answeredCount;

      if (unansweredCount > 0) {
        const confirmMsg = `تنبيه:\nلديك (${unansweredCount}) أسئلة لم تقم بالإجابة عليها!\n\nوفق نظام العلامات السالبة، الأسئلة المتروكة فارغة لا تخصم درجات (تحصل فيها على 0).\n\nهل أنت متأكد من تسليم الاختبار الآن؟`;
        if (!confirm(confirmMsg)) {
          e.preventDefault();
          return false;
        }
      } else {
        if (!confirm("لقد أجبت على جميع الأسئلة الـ " + totalQuestions + ".\nهل أنت متأكد من تسليم الاختبار؟")) {
          e.preventDefault();
          return false;
        }
      }

      document.getElementById("submitBtn").disabled = true;
      document.getElementById("submitBtn").textContent = "جاري تسليم الإجابات...";
      return true;
    }
  </script>
</body>
</html>