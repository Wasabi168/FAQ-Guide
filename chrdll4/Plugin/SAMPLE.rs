
init {

    $SHZ 50000;
}

fn drawLines() {
	
	let N = 100, x0 = 0, y0 = 0, R = 2
	for i in range(0, N) {
		let ang = M_PI*2*i / N
		
		waitUsec(10000)
		let X = R*cos(ang), Y = R*sin(ang)
		line(x0 - X, y0 - Y, x0 + X, y0 + Y, numPts = 500)
	}
}


fn main(scanFreq = 10000) {

//  	while(2) {
//		drawCircle(3,4)
//		let a = M_PI * cos(M_E)
//		drawZZZ(a, a * hypot(a, 0.2))
//	}

	//drawPoly()
	
	let Nx = 1, Ny = 1, D = 10, 
        sizeX = 50, sizeY = 50, ncols=200, nrows=200
		
    rect(-sizeX, -sizeY, sizeX, sizeY, nrows=nrows, nCols=ncols, waitAtEnd = 5000, label="rectZZZ")
	
//	correction(1,1)
//	rect(-sizeX, -sizeY, sizeX, sizeY, nrows=nrows, nCols=ncols, waitAtEnd = 5000, label="zrect")
		
	//rect(-8, -8, -2, -2, nrows=nrows, nCols=ncols, waitAtEnd = 5000, label="rect")	
	//rect(-3, -8, 3, -2, nrows=nrows, nCols=ncols, waitAtEnd = 5000, label="rect")	
	
//	for y in range(0, Ny) {
//		for x in range(0, Nx) {
			
//			let x0 = D*(x / Nx - 0.5),
//				y0 = D*(y / Ny - 0.5)
				
//			//ellipse(x0, y0, 5, 3, angle=30, numPts=10000, nturns=5)
				
//			//rect(x0-sizeX, y0-sizeY, x0+sizeX, y0+sizeY, nrows=nrows, nCols=ncols, waitAtEnd = 5000, label="rect")
//			//drawCircle(y0,x0)
//			//drawZZZ(x0,y0)
//		}
//	}

}
