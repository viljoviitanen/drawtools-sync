all:
	@echo "usage: make update|run"
run:
	( cd ..; ./dev_appserver.py --host 0.0.0.0 --log_level debug drawtools-sync )
update:
	( cd ..; ./appcfg.py update drawtools-sync )
