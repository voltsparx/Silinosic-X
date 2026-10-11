function initConsoleDemo() {
  const button = document.querySelector("[data-demo-run]");
  const status = document.querySelector("[data-demo-status]");
  const output = document.querySelector("[data-demo-output]");
  const meter = document.querySelector("[data-demo-meter]");
  if (!button || !status || !output || !meter) return;

  button.addEventListener("click", () => {
    button.disabled = true;
    button.textContent = "RUNNING...";
    status.textContent = "collecting";
    status.classList.add("is-running");
    output.textContent = "normalizing entities...";
    meter.style.width = "38%";

    window.setTimeout(() => {
      output.textContent = "correlating profile + surface signals...";
      meter.style.width = "72%";
    }, 700);

    window.setTimeout(() => {
      output.textContent = "reporter artifact ready / 4 lanes fused";
      status.textContent = "ready";
      status.classList.remove("is-running");
      meter.style.width = "100%";
      button.disabled = false;
      button.textContent = "RUN SAMPLE CASE";
    }, 1500);
  });
}

document.addEventListener("DOMContentLoaded", initConsoleDemo);
