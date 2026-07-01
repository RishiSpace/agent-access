// AI-SystemAssist Landing Page - Interactive Demo

let isProcessing = false;

function simulateCommand(command) {
    if (isProcessing) return;
    
    const requestDisplay = document.getElementById('request-display');
    const responseDisplay = document.getElementById('response-display');
    
    isProcessing = true;
    
    // Show request
    requestDisplay.innerHTML = `<span class="text-gray-400">$</span> curl -X POST -d '${command}' \\
  -H "X-Agent-Token: your-token" \\
  http://localhost:8765/execute`;
    
    responseDisplay.innerHTML = `<span class="text-gray-500">Sending request...</span>`;
    
    // Simulate network delay
    setTimeout(() => {
        const response = generateMockResponse(command);
        
        responseDisplay.innerHTML = '';
        
        const pre = document.createElement('pre');
        pre.className = 'text-sm leading-relaxed';
        pre.innerHTML = syntaxHighlightJSON(JSON.stringify(response, null, 2));
        
        responseDisplay.appendChild(pre);
        
        // Add a little success flash
        responseDisplay.style.borderColor = 'rgba(52, 211, 153, 0.3)';
        setTimeout(() => {
            responseDisplay.style.borderColor = 'rgba(255,255,255,0.1)';
        }, 800);
        
        isProcessing = false;
    }, 650);
}

function runCustomCommand() {
    const input = document.getElementById('custom-command');
    const command = input.value.trim();
    
    if (!command || isProcessing) return;
    
    simulateCommand(command);
}

function generateMockResponse(command) {
    const timestamp = Date.now();
    
    if (command.includes('whoami')) {
        return {
            command: command,
            success: true,
            returncode: 0,
            stdout: "rishi\n",
            stderr: "",
            duration: 0.012
        };
    }
    
    if (command.includes('ls -la')) {
        return {
            command: command,
            success: true,
            returncode: 0,
            stdout: "total 28\ndrwxr-xr-x  5 rishi rishi  160 Jan 12 14:22 .\ndrwxr-xr-x  4 rishi rishi  128 Jan  5 09:11 ..\n-rw-r--r--  1 rishi rishi  234 Dec 18 11:44 README.md\n-rw-r--r--  1 rishi rishi  512 Jan 12 14:20 pyproject.toml\ndrwxr-xr-x  4 rishi rishi  128 Jan 12 13:44 ai_systemassist\n",
            stderr: "",
            duration: 0.008
        };
    }
    
    if (command.includes('df -h')) {
        return {
            command: command,
            success: true,
            returncode: 0,
            stdout: "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       475G  312G  163G  66% /\n/dev/sdb1       1.8T  1.2T  580G  68% /media/data\n",
            stderr: "",
            duration: 0.021
        };
    }
    
    if (command.includes('uptime')) {
        return {
            command: command,
            success: true,
            returncode: 0,
            stdout: " 14:41:09 up 17 days,  3:19,  2 users,  load average: 1.42, 0.98, 0.74\n",
            stderr: "",
            duration: 0.005
        };
    }
    
    if (command.includes('cat /etc/os-release')) {
        return {
            command: command,
            success: true,
            returncode: 0,
            stdout: "NAME=\"Ubuntu\"\nVERSION=\"22.04.3 LTS (Jammy Jellyfish)\"\nID=ubuntu\nID_LIKE=debian\nPRETTY_NAME=\"Ubuntu 22.04.3 LTS\"\n",
            stderr: "",
            duration: 0.014
        };
    }
    
    // Generic fallback
    return {
        command: command,
        success: true,
        returncode: 0,
        stdout: "Command executed successfully.\n",
        stderr: "",
        duration: Math.random() * 0.08 + 0.004
    };
}

function syntaxHighlightJSON(json) {
    return json
        .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?)/g, function (match) {
            let cls = 'json-string';
            if (/:$/.test(match)) {
                cls = 'json-key';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        })
        .replace(/(\b(true|false|null)\b)/g, '<span class="text-purple-400">$1</span>')
        .replace(/(\b-?\d+\.?\d*\b)/g, '<span class="json-number">$1</span>');
}

// Add some entrance animation to feature cards
function initializeFeatureCards() {
    const cards = document.querySelectorAll('.feature-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
            card.style.transitionDelay = (index * 60) + 'ms';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 400);
    });
}

// Keyboard support
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Press '?' to focus custom command
        if (e.key === '?' && document.activeElement.tagName === 'BODY') {
            e.preventDefault();
            const input = document.getElementById('custom-command');
            if (input) {
                input.focus();
                input.select();
            }
        }
        
        // Escape clears terminal
        if (e.key === 'Escape') {
            const req = document.getElementById('request-display');
            const res = document.getElementById('response-display');
            
            if (document.activeElement === req || document.activeElement === res) {
                req.innerHTML = 'Waiting for command...';
                res.innerHTML = '<span class="text-gray-500">No response yet.</span>';
            }
        }
    });
    
    // Add placeholder hint
    const input = document.getElementById('custom-command');
    if (input) {
        input.addEventListener('focus', function() {
            if (input.value === 'hostname') {
                input.value = '';
            }
        });
        
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                runCustomCommand();
            }
        });
    }
}

// Initialize everything
function initializeWebsite() {
    initializeFeatureCards();
    initializeKeyboardShortcuts();
    
    // Show welcome message in terminal
    setTimeout(() => {
        const res = document.getElementById('response-display');
        if (res && res.innerHTML.includes('No response yet')) {
            res.innerHTML = `
                <div class="text-gray-400 text-xs">Ready. Click any command on the left to simulate execution.</div>
            `;
        }
    }, 2200);
    
    // Optional: Auto-demo one command after a few seconds
    // setTimeout(() => {
    //     if (!isProcessing) {
    //         const req = document.getElementById('request-display');
    //         if (req.innerHTML.includes('Waiting')) {
    //             simulateCommand('uptime');
    //         }
    //     }
    // }, 4500);
    
    console.log('%c[AI-SystemAssist] Modern landing page initialized', 'color:#64748b');
}

// Boot
window.addEventListener('load', initializeWebsite);