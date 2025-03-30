all:
	rm -rf tactilev2.bin
	mv tactilev2.binary tactilev2.bin
	st-flash --reset write tactilev2.bin 0x8000000

clean:
	rm -rf tactilev2.bin
	rm -rf tactilev2.binary

upload:
	st-flash --reset write tactilev2.bin 0x8000000

