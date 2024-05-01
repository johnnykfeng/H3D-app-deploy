# from single_csv_dashboard import create_app
from single_csv_dashboard_refactor import create_app

if __name__ == "__main__":
	app = create_app()
	# use host='0.0.0.0' and port=8080 to run the app on Replit
	app.run_server(debug=True, host='0.0.0.0', port=8080, use_reloader=False)
	