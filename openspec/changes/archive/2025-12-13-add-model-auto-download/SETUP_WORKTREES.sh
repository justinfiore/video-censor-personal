#!/bin/bash
# Setup git worktrees for parallel development of Model Auto-Download feature
# Run this once from the project root to initialize all 7 worktrees

set -e  # Exit on error

PROJECT_ROOT="/Users/justinfiore/workspace/personal/video-censor-personal"
WORKSPACE_PARENT=$(dirname "$PROJECT_ROOT")

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Model Auto-Download: Parallel Worktree Setup                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Ensure we're in the right directory
cd "$PROJECT_ROOT" || exit 1

echo "Project root: $PROJECT_ROOT"
echo "Worktree parent: $WORKSPACE_PARENT"
echo ""

# Create tracking branches if they don't exist
echo "Setting up tracking branches..."

for branch in stream-a/config-schema stream-b/model-manager stream-c/cli-integration \
              stream-d/testing stream-e/pipeline-integration \
              stream-f/huggingface-registry stream-g/documentation; do
  if ! git rev-parse --verify "$branch" >/dev/null 2>&1; then
    echo "  Creating branch: $branch"
    git checkout -b "$branch" main
    git checkout main  # Return to main
  else
    echo "  ✓ Branch exists: $branch"
  fi
done

echo ""
echo "Creating worktrees..."

# Stream A: Configuration Schema
echo "  Creating worktree: wt-config-schema"
git worktree add "$WORKSPACE_PARENT/wt-config-schema" stream-a/config-schema 2>/dev/null || \
  echo "    (Already exists)"

# Stream B: Model Manager
echo "  Creating worktree: wt-model-manager"
git worktree add "$WORKSPACE_PARENT/wt-model-manager" stream-b/model-manager 2>/dev/null || \
  echo "    (Already exists)"

# Stream C: CLI Integration
echo "  Creating worktree: wt-cli-integration"
git worktree add "$WORKSPACE_PARENT/wt-cli-integration" stream-c/cli-integration 2>/dev/null || \
  echo "    (Already exists)"

# Stream D: Testing
echo "  Creating worktree: wt-testing"
git worktree add "$WORKSPACE_PARENT/wt-testing" stream-d/testing 2>/dev/null || \
  echo "    (Already exists)"

# Stream E: Pipeline Integration
echo "  Creating worktree: wt-pipeline-integration"
git worktree add "$WORKSPACE_PARENT/wt-pipeline-integration" stream-e/pipeline-integration 2>/dev/null || \
  echo "    (Already exists)"

# Stream F: Hugging Face Registry
echo "  Creating worktree: wt-huggingface-registry"
git worktree add "$WORKSPACE_PARENT/wt-huggingface-registry" stream-f/huggingface-registry 2>/dev/null || \
  echo "    (Already exists)"

# Stream G: Documentation
echo "  Creating worktree: wt-documentation"
git worktree add "$WORKSPACE_PARENT/wt-documentation" stream-g/documentation 2>/dev/null || \
  echo "    (Already exists)"

echo ""
echo "✓ Worktree setup complete!"
echo ""
echo "Available worktrees:"
git worktree list | grep -E "config-schema|model-manager|cli-integration|testing|pipeline-integration|huggingface-registry|documentation" || true

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps for each subagent:"
echo ""
echo "Stream A (Config Schema):"
echo "  cd $WORKSPACE_PARENT/wt-config-schema"
echo "  # Implement tasks 1.1-1.5"
echo "  git commit -m 'Add model auto-download configuration schema'"
echo "  git push origin stream-a/config-schema"
echo ""
echo "Stream B (Model Manager):"
echo "  cd $WORKSPACE_PARENT/wt-model-manager"
echo "  # Implement tasks 2.1-2.8, 8.1-8.5"
echo "  git commit -m 'Add model manager with download, retry, checksum'"
echo "  git push origin stream-b/model-manager"
echo ""
echo "Stream C (CLI Integration):"
echo "  cd $WORKSPACE_PARENT/wt-cli-integration"
echo "  # Implement tasks 3.1-3.4"
echo "  git commit -m 'Add --download-models CLI flag'"
echo "  git push origin stream-c/cli-integration"
echo ""
echo "Stream D (Testing):"
echo "  cd $WORKSPACE_PARENT/wt-testing"
echo "  # Implement tasks 8.x, 9.x, 10.x as features merge"
echo "  git commit -m 'Add unit, integration, and E2E tests'"
echo "  git push origin stream-d/testing"
echo ""
echo "Stream E (Pipeline Integration):"
echo "  cd $WORKSPACE_PARENT/wt-pipeline-integration"
echo "  # Implement tasks 4.1-4.5, 5.1-5.3 (after Phase 1 merges)"
echo "  git commit -m 'Integrate model auto-download into pipeline'"
echo "  git push origin stream-e/pipeline-integration"
echo ""
echo "Stream F (Hugging Face Registry):"
echo "  cd $WORKSPACE_PARENT/wt-huggingface-registry"
echo "  # Implement tasks 6.1-6.4, 7.1-7.5 (after Phase 2 merges)"
echo "  git commit -m 'Add Hugging Face model registry integration'"
echo "  git push origin stream-f/huggingface-registry"
echo ""
echo "Stream G (Documentation):"
echo "  cd $WORKSPACE_PARENT/wt-documentation"
echo "  # Implement tasks 11.1-11.6, 12.1-12.3 (parallel)"
echo "  git commit -m 'Add model auto-download documentation'"
echo "  git push origin stream-g/documentation"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "To merge a stream after review:"
echo "  cd $PROJECT_ROOT"
echo "  git checkout main"
echo "  git merge stream-X/[name]"
echo "  git push origin main"
echo "  git worktree remove $WORKSPACE_PARENT/wt-[name]"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "✅ Setup complete! Subagents can now begin implementation."
echo ""
