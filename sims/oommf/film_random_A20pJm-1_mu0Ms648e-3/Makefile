sims:
	for RS in 42 4242 424242 24 2424; do \
		oommf boxsi -threads 8 -parameters \
			"RSEED $${RS} BASENAME oommf_film_random_rseed$${RS}" \
			oommf_film_random.mif; \
	done
