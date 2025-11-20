const backendBase = "http://127.0.0.1:8000"; // адрес FastAPI

const promptEl = document.getElementById("prompt");
const sendBtn = document.getElementById("sendBtn");
const answerEl = document.getElementById("answer");
const statsEl = document.getElementById("stats");
const logsEl = document.getElementById("logs");

async function fetchStats() {
	try {
		const resp = await fetch(`${backendBase}/api/stats`);
		const data = await resp.json();
		statsEl.textContent =
			`Всего запросов: ${data.total_requests}, ` +
			`суммарная длина ответов: ${data.total_output_chars} символов, ` +
			`запросов сегодня: ${data.today_requests}`;
	} catch (e) {
		statsEl.textContent = "Ошибка загрузки статистики";
		console.error(e);
	}
}

async function fetchLogs() {
	try {
		const resp = await fetch(`${backendBase}/api/logs?limit=10`);
		const data = await resp.json();
		logsEl.innerHTML = "";
		data.forEach(item => {
			const li = document.createElement("li");
			li.textContent = `[${item.created_at}] ${item.prompt} → ${item.response.slice(0, 60)}...`;
			logsEl.appendChild(li);
		});
	} catch (e) {
		console.error(e);
	}
}

async function sendPrompt() {
	const prompt = promptEl.value.trim();
	if (!prompt) return;

	answerEl.textContent = "";      // очищаем старый ответ
	sendBtn.disabled = true;
	sendBtn.textContent = "Ждем ответ...";

	try {
		const resp = await fetch(`${backendBase}/api/chat`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({ prompt }),
		});

		if (!resp.ok || !resp.body) {
			answerEl.textContent = `Ошибка: ${resp.status}`;
			return;
		}

		const reader = resp.body.getReader();
		const decoder = new TextDecoder();

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			const chunkText = decoder.decode(value, { stream: true });
			answerEl.textContent += chunkText;
		}

		// Когда стрим закончился, обновляем статистику и логи
		await fetchStats();
		await fetchLogs();
	} catch (err) {
		console.error(err);
		answerEl.textContent = "Произошла ошибка при запросе.";
	} finally {
		sendBtn.disabled = false;
		sendBtn.textContent = "Спросить";
	}
}

sendBtn.addEventListener("click", sendPrompt);

// Стартовая загрузка статистики и логов
fetchStats();
fetchLogs();
