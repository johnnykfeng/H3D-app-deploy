from single_csv_dashboard import main

if __name__ == "__main__":
	app = main()
	# app.run_server(debug=True, port=8080, use_reloader=False)
	app.run_server(debug=True, host='0.0.0.0', port=8080, use_reloader=False)
	