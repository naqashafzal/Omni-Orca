# Mouse Control & Advanced Actions - Quick Guide

## 🖱️ New Mouse Control Features

The Neural Automater now supports advanced mouse and keyboard controls!

### Available Actions

#### 1. **Mouse Click at Coordinates**
```python
mouse_click(x, y, button="left", click_count=1)
```
- Click anywhere on the page by pixel coordinates
- Supports left, right, and middle mouse buttons
- Can do single or double clicks

**Example Commands:**
- "Click at position 500, 300"
- "Right-click at coordinates 100, 200"
- "Double-click at 800, 400"

#### 2. **Hover**
```python
hover(selector)
```
- Hover over elements to reveal dropdown menus
- Useful for navigation menus

**Example:**
- "Hover over the menu button"

#### 3. **Right-Click**
```python
right_click(selector)
```
- Open context menus
- Perfect for browser extension management

**Example:**
- "Right-click the extension icon"

#### 4. **Double-Click**
```python
double_click(selector)
```
- Double-click elements

#### 5. **Scroll**
```python
scroll(x, y)
```
- Scroll the page
- x = horizontal scroll, y = vertical scroll

**Examples:**
- "Scroll down 500 pixels" → scroll(0, 500)
- "Scroll up 300 pixels" → scroll(0, -300)

#### 6. **Press Keys**
```python
press_key(key)
```
- Press any keyboard key
- Useful for shortcuts

**Examples:**
- press_key("Enter")
- press_key("Escape")
- press_key("Tab")
- press_key("Control+T") - New tab

---

## 🔧 Installing Browser Extensions

Now you can automate installing extensions! Here's how:

### Method 1: Using Auto-Pilot

```
Enable auto-pilot and say:
"Go to Chrome Web Store, search for uBlock Origin, and install it"
```

The AI will:
1. Navigate to chrome://extensions or the web store
2. Click the install button
3. Confirm installation

### Method 2: Manual Commands

```
1. "Navigate to chrome://extensions"
2. "Click the developer mode toggle"
3. "Click load unpacked"
4. (Use file dialog)
```

---

## 📝 Example Use Cases

### 1. Installing Extension
```
Auto-pilot: "Install the React DevTools extension from Chrome Web Store"
```

### 2. Opening Context Menu
```
"Right-click the page and select 'Inspect'"
```

### 3. Navigating Dropdown Menus
```
"Hover over Settings, then click Privacy"
```

### 4. Scrolling to Bottom
```
"Scroll to the bottom of the page"
```

### 5. Keyboard Shortcuts
```
"Press Ctrl+T to open new tab"
"Press Escape to close dialog"
```

---

## 🎯 Tips for Best Results

1. **Use Coordinates for Tricky Elements**: If selectors don't work, use pixel coordinates
2. **Hover Before Click**: Some menus need hover first
3. **Wait Between Actions**: Add wait(1) between complex actions
4. **Use Keyboard Shortcuts**: Faster than clicking menus

---

## 🚀 Advanced Automation Examples

### Example 1: Complex Navigation
```json
[
  { "action": "navigate", "url": "https://example.com" },
  { "action": "hover", "selector": "#menu" },
  { "action": "wait", "seconds": 0.5 },
  { "action": "click", "selector": "#submenu-item" }
]
```

### Example 2: Form Filling with Keyboard
```json
[
  { "action": "click", "selector": "#name" },
  { "action": "type", "selector": "#name", "text": "John Doe" },
  { "action": "press_key", "key": "Tab" },
  { "action": "type", "selector": "#email", "text": "john@example.com" },
  { "action": "press_key", "key": "Enter" }
]
```

### Example 3: Right-Click Menu
```json
[
  { "action": "right_click", "selector": "img" },
  { "action": "wait", "seconds": 0.3 },
  { "action": "press_key", "key": "ArrowDown" },
  { "action": "press_key", "key": "Enter" }
]
```

---

## 🎮 All Supported Actions

| Action | Description | Example |
|--------|-------------|---------|
| navigate | Go to URL | `navigate("https://google.com")` |
| click | Click element | `click("button")` |
| type | Type text | `type("#input", "hello")` |
| mouse_click | Click coordinates | `mouse_click(500, 300)` |
| mouse_move | Move mouse | `mouse_move(100, 200)` |
| hover | Hover element | `hover("#menu")` |
| right_click | Right-click | `right_click("img")` |
| double_click | Double-click | `double_click("file")` |
| scroll | Scroll page | `scroll(0, 500)` |
| press_key | Press key | `press_key("Enter")` |
| wait | Wait seconds | `wait(2)` |

---

## 💡 Pro Tips

1. **Extension Installation**: Use Chrome Web Store URL directly
2. **Developer Mode**: Enable via chrome://extensions for manual installs
3. **Coordinates**: Use browser DevTools to find pixel positions
4. **Recording**: All mouse actions are recorded and can be replayed!

Enjoy your enhanced automation capabilities! 🚀
