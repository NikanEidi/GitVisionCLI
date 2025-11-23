# 📝 Changelog

All notable changes to GitVisionCLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2024-11-23

### 🎉 **Initial Release**

The first stable release of GitVisionCLI!

### ✨ **Added**

#### **Core Features**
- AI-powered terminal IDE with dual-panel interface
- Natural language file editing (no clarification loops!)
- Complete Git workflow integration
- Direct GitHub repository management
- Multi-model AI support (OpenAI, Claude, Gemini, Ollama)

#### **File Operations**
- Create files with single-line or multiline content
- Edit files with natural language commands
- Delete, rename, and read files
- Transactional operations with rollback

#### **Line Editing**
- `remove line N` - Delete specific line
- `add line N with TEXT` - Insert line
- `edit line N with TEXT` - Replace line
- `delete lines N-M` - Remove range
- All variations (delete/remove, add/insert, edit/replace/update)

#### **Git Features**
- Full Git workflow (init, add, commit, push, pull)
- Branch management (create, checkout, merge)
- Visual commit graph (`:git-graph`)
- Real-time Git status
- Integrated diff viewing

#### **GitHub Integration**
- Create private/public repositories
- Create issues with titles and bodies
- Create pull requests
- Automatic authentication via token

#### **UI Panels**
- Banner panel (`:banner`) - Quick commands
- Sheet panel (`:sheet`) - Full reference
- Tree panel (`:tree`) - File browser
- Git graph panel (`:git-graph`) - Visual history
- Editor panel (`:edit`) - Line-numbered editing

#### **AI Capabilities**
- Natural language code analysis
- Bug detection and suggestions
- Code refactoring recommendations
- Test file generation
- Model switching (`:set-ai`)

### 🔧 **Fixed**

- ✅ Eliminated "Please specify file and line numbers" clarification loops
- ✅ Fixed duplicate panel rendering (full screen clear)
- ✅ Fixed banner logo visibility (compact layout)
- ✅ Fixed file content normalization (UTF-8, newlines)
- ✅ Fixed multiline input handling (`:ml` ... `:end`)

### 🎨 **Improved**

- Enhanced system prompts for deterministic AI behavior
- Optimized natural language mapper with pattern recognition
- Improved editing engine with transaction management
- Polished dual-panel rendering (no flicker)
- Better error messages and user feedback

### 📚 **Documentation**

- Comprehensive README.md with badges and mermaid diagrams
- Quick start guide (docs/QUICKSTART.md)
- Complete command reference (docs/COMMANDS.md)
- Feature deep-dive (docs/FEATURES.md)
- Contributing guidelines (CONTRIBUTING.md)
- Testing guide (TESTING_GUIDE.md)
- Cheat sheet (CHEAT_SHEET.md)

### 🧹 **Cleanup**

- Removed unnecessary demo files
- Updated .gitignore with complete excludes
- Organized docs/ folder structure
- Cleaned up temporary test artifacts

---

## **[Unreleased]**

### 🔮 **Planned**

- Syntax highlighting in editor
- Plugin system for extensions
- Collaborative editing features
- Custom AI prompt templates
- Enhanced Git visualization
- Conflict resolution UI
- Performance profiling tools

---

## **Version History**

| Version | Date | Highlights |
|---------|------|------------|
| **1.0.0** | 2024-11-23 | 🎉 Initial stable release |

---

**For upgrade instructions, see [QUICKSTART.md](docs/QUICKSTART.md)**
