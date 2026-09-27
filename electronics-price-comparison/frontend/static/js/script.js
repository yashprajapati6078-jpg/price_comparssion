/* ==========================================================================
   ElectroCompare - 3D Animation & Interactive Client Scripts
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    
    // 1. Top 3D Scroll Progress Bar Indicator
    const progressBar = document.getElementById('scrollProgressBar');
    if (progressBar) {
        window.addEventListener('scroll', function () {
            const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            progressBar.style.width = scrolled + '%';
        });
    }

    // 2. IntersectionObserver for 3D Scroll Reveal Animations (.reveal-3d)
    const revealElements = document.querySelectorAll('.reveal-3d');
    if (revealElements.length > 0) {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                }
            });
        }, observerOptions);

        revealElements.forEach(el => revealObserver.observe(el));
    }

    // Auto-add .reveal-3d to product cards, category cards, and section containers
    document.querySelectorAll('.product-card, .category-card, .feature-box').forEach((card, index) => {
        if (!card.classList.contains('reveal-3d')) {
            card.classList.add('reveal-3d');
            if (index % 4 === 1) card.classList.add('delay-1');
            if (index % 4 === 2) card.classList.add('delay-2');
            if (index % 4 === 3) card.classList.add('delay-3');
        }
    });

    // Re-observe auto-tagged elements
    document.querySelectorAll('.reveal-3d').forEach(el => {
        const obs = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                }
            });
        }, { threshold: 0.08 });
        obs.observe(el);
    });

    // 3. Interactive 3D Card Mouse Tilt Effect (.product-card, .category-card)
    const tiltCards = document.querySelectorAll('.product-card, .category-card');
    tiltCards.forEach(card => {
        card.addEventListener('mousemove', function (e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = ((y - centerY) / centerY) * -8;
            const rotateY = ((x - centerX) / centerX) * 8;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px) scale(1.02)`;
        });

        card.addEventListener('mouseleave', function () {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px) scale(1)`;
        });
    });

    // 4. Image Gallery Thumbnail Switcher on Product Details
    const mainProductImg = document.getElementById('mainProductImage');
    const thumbnails = document.querySelectorAll('.product-thumb-img, .thumbnail-img');

    if (mainProductImg && thumbnails.length > 0) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function () {
                thumbnails.forEach(t => t.classList.remove('border-primary', 'active'));
                this.classList.add('border-primary', 'active');
                mainProductImg.src = this.dataset.src || this.src;
            });
        });
    }

    // 5. Smooth scroll for internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.startsWith('#')) {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // 6. Live Market Pulse Header Ticker Stream
    initLiveMarketTicker();

});

// Global Toast Notification Helper
function showToastNotification(title, message, type = 'info') {
    const container = document.getElementById('globalToastContainer');
    if (!container) return;

    const toastId = 'toast-' + Date.now();
    const borderClass = type === 'success' ? 'border-success' : (type === 'danger' ? 'border-danger' : 'border-primary');
    const iconClass = type === 'success' ? 'bi-check-circle-fill text-success' : (type === 'danger' ? 'bi-exclamation-triangle-fill text-danger' : 'bi-info-circle-fill text-primary');

    const toastHtml = `
        <div id="${toastId}" class="toast toast-custom align-items-center ${borderClass} border mb-2 shadow" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-start gap-2.5">
                    <i class="bi ${iconClass} fs-5 flex-shrink-0 mt-0.5"></i>
                    <div>
                        <div class="fw-bold fs-sm text-white">${title}</div>
                        <div class="text-white-50 fs-xs">${message}</div>
                    </div>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.getElementById(toastId);
    if (toastEl && window.bootstrap) {
        const bsToast = new bootstrap.Toast(toastEl, { delay: 4500 });
        bsToast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }
}

// Live Market Pulse Ticker Polling
function initLiveMarketTicker() {
    const tickerContent = document.getElementById('liveTickerContent');
    if (!tickerContent) return;

    function pollMarketPulse() {
        fetch('/api/live/market-pulse')
            .then(res => res.json())
            .then(data => {
                if (data.pulse && data.pulse.length > 0) {
                    tickerContent.innerHTML = data.pulse.map(item => {
                        const isDown = item.direction === 'down';
                        const badgeBg = isDown ? 'bg-success' : (item.direction === 'up' ? 'bg-danger' : 'bg-secondary');
                        const icon = isDown ? 'bi-arrow-down-left' : (item.direction === 'up' ? 'bi-arrow-up-right' : 'bi-dash');
                        return `
                            <a href="/product/${item.product_id}" class="live-ticker-item">
                                <span class="badge ${badgeBg} text-white rounded-pill px-2 py-0.5"><i class="bi ${icon} me-0.5"></i>${item.badge_text}</span>
                                <strong class="text-white">${item.retailer}:</strong>
                                <span>${item.brand} ${item.name}</span>
                                <span class="fw-bold text-warning">₹${Number(item.current_price).toLocaleString('en-IN')}</span>
                                <span class="text-white-50 fs-xxs">(${item.time_ago})</span>
                            </a>
                        `;
                    }).join('<span class="text-white-50 opacity-25">|</span>');
                }
            })
            .catch(err => console.debug('Ticker poll error:', err));
    }

    // Initial fetch + 20s interval
    pollMarketPulse();
    setInterval(pollMarketPulse, 20000);
}

// =====================================================================
// RIGRATE AI ASSISTANT CLIENT (POWERED BY YASH)
// =====================================================================
let rigrateAiHistory = [];

function initRigRateAiWidget() {
    const launcher = document.getElementById('rigrateAiLauncherBtn');
    const chatWin = document.getElementById('rigrateAiChatWindow');
    const minimizeBtn = document.getElementById('rigrateAiMinimizeBtn');
    const clearBtn = document.getElementById('rigrateAiClearBtn');
    const input = document.getElementById('rigrateAiInput');
    const bubble = document.getElementById('rigrateAiPromptBubble');
    const bubbleClose = document.getElementById('rigrateAiBubbleClose');

    if (!launcher || !chatWin) return;

    // Show popup bubble after 2 seconds if not dismissed
    const bubbleDismissed = sessionStorage.getItem('rigrateAiBubbleDismissed');
    if (bubble && !bubbleDismissed) {
        setTimeout(() => {
            if (chatWin.classList.contains('d-none')) {
                bubble.classList.remove('d-none');
            }
        }, 1800);
    } else if (bubble) {
        bubble.classList.add('d-none');
    }

    // Close popup bubble
    if (bubbleClose && bubble) {
        bubbleClose.addEventListener('click', (e) => {
            e.stopPropagation();
            bubble.classList.add('d-none');
            sessionStorage.setItem('rigrateAiBubbleDismissed', 'true');
        });
    }

    // Toggle open
    launcher.addEventListener('click', () => {
        if (bubble) bubble.classList.add('d-none');
        sessionStorage.setItem('rigrateAiBubbleDismissed', 'true');

        const isHidden = chatWin.classList.contains('d-none');
        if (isHidden) {
            chatWin.classList.remove('d-none');
            input.focus();
        } else {
            chatWin.classList.add('d-none');
        }
    });

    // Handle clicks on popup help options
    document.addEventListener('click', (e) => {
        const selectBtn = e.target.closest('.ai-select-help-btn');
        if (selectBtn) {
            const query = selectBtn.getAttribute('data-query');
            if (bubble) bubble.classList.add('d-none');
            sessionStorage.setItem('rigrateAiBubbleDismissed', 'true');

            // Open chat window and send query
            chatWin.classList.remove('d-none');
            if (input && query) {
                input.value = query;
                window.sendRigRateAiMessage();
            }
        }
    });

    // Minimize
    minimizeBtn.addEventListener('click', () => {
        chatWin.classList.add('d-none');
    });

    // Clear history
    clearBtn.addEventListener('click', () => {
        rigrateAiHistory = [];
        const msgList = document.getElementById('rigrateAiMessagesList');
        if (msgList) {
            msgList.innerHTML = `
                <div class="ai-message-row ai-row-assistant mb-3">
                    <div class="ai-msg-avatar"><i class="bi bi-robot"></i></div>
                    <div class="ai-msg-bubble shadow-xs">
                        <p class="mb-2 fw-semibold">Hi! I'm <strong>RigRate AI</strong> 👋 *(Powered by Yash)*.</p>
                        <p class="mb-2 fs-sm text-secondary">Chat cleared! What electronics or deals would you like to explore?</p>
                    </div>
                </div>
            `;
        }
    });

    // Suggestion pills
    document.addEventListener('click', (e) => {
        const chip = e.target.closest('.ai-chip-btn');
        if (chip) {
            const query = chip.getAttribute('data-query');
            if (query && input) {
                input.value = query;
                window.sendRigRateAiMessage();
            }
        }
    });
}

function parseMarkdownToHtml(text) {
    if (!text) return '';
    let out = text;

    // Tables
    const lines = out.split('\n');
    let inTable = false;
    let tableHtml = '';
    let processedLines = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.startsWith('|') && line.endsWith('|')) {
            if (!inTable) {
                inTable = true;
                tableHtml = '<div class="table-responsive my-2"><table class="table table-sm table-bordered mb-0 bg-white"><tbody>';
            }
            // Skip markdown divider row |---|---|
            if (line.includes('---')) {
                continue;
            }
            const cells = line.split('|').slice(1, -1);
            tableHtml += '<tr>' + cells.map(c => `<td class="p-1 fs-xxs">${c.trim()}</td>`).join('') + '</tr>';
        } else {
            if (inTable) {
                inTable = false;
                tableHtml += '</tbody></table></div>';
                processedLines.push(tableHtml);
            }
            processedLines.push(lines[i]);
        }
    }
    if (inTable) {
        tableHtml += '</tbody></table></div>';
        processedLines.push(tableHtml);
    }
    // Headings
    out = out.replace(/^### (.*$)/gim, '<h6 class="fw-bold text-dark mt-2 mb-1">$1</h6>');
    out = out.replace(/^#### (.*$)/gim, '<div class="fw-bold text-primary mt-2 mb-1 fs-sm">$1</div>');
    
    // Horizontal Rule
    out = out.replace(/^---$/gim, '<hr class="my-2 border-secondary-subtle">');

    // Bold
    out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Strikethrough
    out = out.replace(/~~(.*?)~~/g, '<del class="text-muted fs-xxs">$1</del>');
    // Italics
    out = out.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Links [Text](URL)
    out = out.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="text-primary fw-semibold text-decoration-none hover-underline" target="_blank">$1</a>');
    // Bullet points
    out = out.replace(/^\s*[•\-\*]\s+(.*)$/gm, '<div class="d-flex align-items-start gap-1.5 ms-1 my-0.5"><span class="text-primary">•</span><span>$1</span></div>');
    // Paragraph breaks
    out = out.replace(/\n\n/g, '<br><br>');
    out = out.replace(/\n/g, '<br>');

    return out;
}

window.sendRigRateAiMessage = function() {
    const input = document.getElementById('rigrateAiInput');
    const msgList = document.getElementById('rigrateAiMessagesList');
    const typing = document.getElementById('rigrateAiTypingIndicator');
    const suggestions = document.getElementById('rigrateAiSuggestions');

    if (!input || !msgList) return;
    const userText = input.value.trim();
    if (!userText) return;

    // Hide suggestions after first message
    if (suggestions) suggestions.classList.add('d-none');

    // Append User Bubble
    const userRow = document.createElement('div');
    userRow.className = 'ai-message-row ai-row-user mb-3';
    userRow.innerHTML = `
        <div class="ai-msg-avatar bg-primary"><i class="bi bi-person-fill"></i></div>
        <div class="ai-msg-bubble shadow-xs">${userText.replace(/</g, '&lt;')}</div>
    `;
    msgList.appendChild(userRow);
    input.value = '';
    msgList.scrollTop = msgList.scrollHeight;

    // Show typing
    if (typing) typing.classList.remove('d-none');
    msgList.scrollTop = msgList.scrollHeight;

    // Send to API
    fetch('/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: userText,
            history: rigrateAiHistory
        })
    })
    .then(res => res.json())
    .then(data => {
        if (typing) typing.classList.add('d-none');

        const replyRaw = data.reply || "I didn't receive a response. Please try again.";
        const replyHtml = parseMarkdownToHtml(replyRaw);

        // Append Assistant Bubble
        const assistantRow = document.createElement('div');
        assistantRow.className = 'ai-message-row ai-row-assistant mb-3';
        assistantRow.innerHTML = `
            <div class="ai-msg-avatar"><i class="bi bi-robot"></i></div>
            <div class="ai-msg-bubble shadow-xs">${replyHtml}</div>
        `;
        msgList.appendChild(assistantRow);
        msgList.scrollTop = msgList.scrollHeight;

        // Update history
        rigrateAiHistory.push({ role: 'user', content: userText });
        rigrateAiHistory.push({ role: 'assistant', content: replyRaw });
        if (rigrateAiHistory.length > 10) rigrateAiHistory = rigrateAiHistory.slice(-10);
    })
    .catch(err => {
        if (typing) typing.classList.add('d-none');
        const errRow = document.createElement('div');
        errRow.className = 'ai-message-row ai-row-assistant mb-3';
        errRow.innerHTML = `
            <div class="ai-msg-avatar"><i class="bi bi-robot"></i></div>
            <div class="ai-msg-bubble shadow-xs text-danger">
                Connection error. Please try again!
            </div>
        `;
        msgList.appendChild(errRow);
        msgList.scrollTop = msgList.scrollHeight;
    });
};

document.addEventListener('DOMContentLoaded', () => {
    initRigRateAiWidget();
});


