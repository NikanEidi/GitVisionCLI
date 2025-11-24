# Project Structure

```
GitVisionCLI/
│
├── README.md                    # Main project documentation
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── PROJECT_STRUCTURE.md         # This file - project layout overview
│
├── docs/                        # Documentation
│   ├── README.md                # Documentation index
│   ├── QUICKSTART.md            # 5-minute getting started guide
│   ├── COMMANDS.md              # Full command reference
│   ├── COMMAND_SHEET.md         # Complete command sheet reference
│   ├── FEATURES.md              # In-depth feature overview
│   ├── NATURAL_LANGUAGE_ACTION_ENGINE.md  # Engine documentation
│   ├── RUN_AND_TEST.md          # Testing and validation guide
│   ├── SYSTEM_STATUS.md         # System status report
│   └── PUBLISH_READY.md         # Publish readiness checklist
│
├── tests/                       # Test files and documentation
│   ├── README.md                # Testing overview
│   ├── test_brain.py            # Brain component tests
│   ├── test_chat_engine_and_context.py  # Chat engine tests
│   ├── test_editing_engine.py   # Editing engine tests
│   ├── test_natural_language_mapper.py  # Natural language mapper tests
│   ├── test_provider_normalizer.py  # Provider normalizer tests
│   ├── test_all_scenarios.py    # Original 12 test scenarios
│   ├── test_comprehensive_operations.py  # 44 comprehensive tests
│   ├── test_extensive_natural_language.py  # 193+ natural language variations
│   ├── TEST_EXPANSION_SUMMARY.md  # Test expansion summary
│   ├── TEST_RESULTS_SUMMARY.md    # Test results summary
│   ├── TEST_FIXES_SUMMARY.md      # Test fixes summary
│   └── VERIFY_TESTS.md            # Test verification checklist
│
├── scripts/                     # Utility scripts
│   ├── README.md                # Scripts documentation
│   ├── debug_dry_run.py         # Debug dry-run script
│   ├── validate_improvements.py  # Validation script
│   ├── verify_write.py           # Write verification script
│   └── QUICK_START.sh            # Quick start script
│
├── examples/                    # Example files
│   └── natural_language_action_engine_example.py  # Example usage
│
├── gitvisioncli/                # Main source code package
│   ├── __main__.py              # Entry point
│   ├── cli.py                   # Main CLI interface
│   │
│   ├── config/                  # Configuration
│   │   ├── config.json          # Configuration file
│   │   └── settings.py          # Settings management
│   │
│   ├── core/                    # Core functionality
│   │   ├── __init__.py
│   │   ├── action_router.py     # Action routing
│   │   ├── ai_client.py         # AI client abstraction
│   │   ├── application_controller.py  # Application controller
│   │   ├── brain.py             # Brain component
│   │   ├── chat_engine.py       # Chat engine with streaming
│   │   ├── command_normalizer.py  # Command normalization
│   │   ├── command_router.py    # Command routing
│   │   ├── context_manager.py   # Context management
│   │   ├── doc_sync.py          # Documentation synchronization
│   │   ├── editing_engine.py    # File editing engine
│   │   ├── executor.py          # Action executor
│   │   ├── github_client.py     # GitHub API client
│   │   ├── natural_language_action_engine.py  # Natural language engine
│   │   ├── natural_language_mapper.py  # Natural language mapper
│   │   ├── planner.py           # Planning component
│   │   ├── provider_normalizer.py  # Provider normalization
│   │   ├── safe_patch_engine.py # Safe patch engine
│   │   ├── supervisor.py        # Action supervisor
│   │   ├── terminal.py          # Terminal interface
│   │   │
│   │   ├── ai/                  # AI providers
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base provider interface
│   │   │   ├── factory.py       # Provider factory
│   │   │   └── openai_provider.py  # OpenAI provider
│   │   │
│   │   ├── execution/           # Execution handlers
│   │   │   ├── __init__.py
│   │   │   ├── base_executor.py # Base executor
│   │   │   ├── executor_factory.py  # Executor factory
│   │   │   ├── file_executor.py # File operations executor
│   │   │   ├── git_executor.py  # Git operations executor
│   │   │   ├── github_executor.py  # GitHub operations executor
│   │   │   └── shell_executor.py  # Shell commands executor
│   │   │
│   │   ├── file_handlers/       # File operation handlers
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base handler
│   │   │   ├── append_handler.py  # Append operations
│   │   │   ├── delete_handler.py  # Delete operations
│   │   │   ├── insert_handler.py  # Insert operations
│   │   │   └── replace_handler.py  # Replace operations
│   │   │
│   │   ├── handlers/            # Action handlers
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base handler
│   │   │   ├── file_handlers.py # File operation handlers
│   │   │   ├── git_handlers.py  # Git operation handlers
│   │   │   ├── github_handlers.py  # GitHub operation handlers
│   │   │   ├── manager.py       # Handler manager
│   │   │   ├── registry.py     # Handler registry
│   │   │   └── README.md        # Handlers documentation
│   │   │
│   │   └── strategies/         # Strategy patterns
│   │       ├── __init__.py
│   │       ├── provider_strategy.py  # Provider strategy
│   │       └── streaming_strategy.py  # Streaming strategy
│   │
│   ├── features/                # Feature modules
│   │   ├── code_review.py       # Code review feature
│   │   ├── project_generator.py # Project generator
│   │   └── readme_gen.py        # README generator
│   │
│   ├── plugins/                 # Plugin system
│   │   ├── __init__.py
│   │   ├── base_plugin.py       # Base plugin interface
│   │   ├── plugin_manager.py    # Plugin manager
│   │   └── registry.py          # Plugin registry
│   │
│   ├── services/                # Service layer
│   │   ├── __init__.py
│   │   ├── config_service.py    # Configuration service
│   │   ├── file_service.py      # File operations service
│   │   ├── git_service.py       # Git operations service
│   │   └── validation_service.py  # Validation service
│   │
│   ├── ui/                      # UI components
│   │   ├── __init__.py
│   │   ├── banner.py            # Banner display
│   │   ├── chat_box.py          # Chat box component
│   │   ├── colors.py            # Color definitions
│   │   ├── dual_panel.py        # Dual panel layout
│   │   ├── glitch_effects.py    # Visual effects
│   │   │
│   │   └── components/          # UI component library
│   │       ├── __init__.py
│   │       ├── base_component.py  # Base component
│   │       ├── panel_component.py  # Panel component
│   │       └── renderer_component.py  # Renderer component
│   │
│   ├── utils/                   # Utility functions
│   │   ├── file_ops.py          # File operations utilities
│   │   ├── git_detect.py        # Git detection utilities
│   │   ├── path_utils.py        # Path utilities
│   │   └── validator.py         # Validation utilities
│   │
│   └── workspace/               # Workspace UI components
│       ├── __init__.py
│       ├── banner_panel.py     # Banner panel
│       ├── editor_panel.py      # Code editor panel
│       ├── fs_watcher.py        # File system watcher
│       ├── git_graph_panel.py   # Git graph visualization
│       ├── markdown_panel.py    # Markdown renderer panel
│       ├── model_manager_panel.py  # Model manager panel
│       ├── panel_manager.py     # Panel state manager
│       ├── right_panel.py       # Right panel container
│       ├── sheet_panel.py       # Command sheet panel
│       └── tree_panel.py        # File tree panel
│
├── pyproject.toml               # Project configuration
├── build/                       # Build artifacts (generated)
└── gitvisioncli.egg-info/       # Package metadata (generated)
```

## Directory Overview

### Root Level
- **README.md**: Main project documentation and introduction
- **CHANGELOG.md**: Version history and release notes
- **CONTRIBUTING.md**: Guidelines for contributors
- **PROJECT_STRUCTURE.md**: This file - project layout reference

### docs/
All documentation files organized in one place:
- User guides (QUICKSTART, COMMANDS, FEATURES)
- Technical documentation (NATURAL_LANGUAGE_ACTION_ENGINE)
- Testing guides (RUN_AND_TEST)
- Status reports (SYSTEM_STATUS, PUBLISH_READY)

### tests/
All test files and test-related documentation:
- Unit tests for core components
- Integration test scenarios
- Test summaries and verification checklists

### scripts/
Utility scripts for development and maintenance:
- Debug scripts
- Validation scripts
- Quick start scripts

### gitvisioncli/
Main source code package organized by functionality:
- **core/**: Core engine, AI integration, action handling
- **ui/**: User interface components
- **workspace/**: Workspace panels and management
- **features/**: Feature modules
- **services/**: Service layer abstractions
- **utils/**: Utility functions
- **plugins/**: Plugin system

## Key Design Principles

1. **Separation of Concerns**: Core logic, UI, and utilities are clearly separated
2. **Modularity**: Features and plugins are modular and extensible
3. **Documentation**: All documentation is centralized in `docs/`
4. **Testing**: All tests are organized in `tests/` with related documentation
5. **Scripts**: Utility scripts are organized in `scripts/`
