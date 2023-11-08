PRE_PUSH_SCRIPT := pre-push

GIT_HOOKS_DIR := .git/hooks

set:
	@echo "Setting pre-push file"
	@mv $(PRE_PUSH_SCRIPT) $(GIT_HOOKS_DIR)/
	@chmod +x $(GIT_HOOKS_DIR)/pre-push
	@echo "done."


