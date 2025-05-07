
/*fn drawCircleX() {
	
	shape(label="circle") { // beginning of the scan box..
		let rX = 5, rY = 5
		moveTo(rX, 0)
		startMeasure()
		for i in range(0, 720*10) { 
			let a = i*M_PI/180
			let xx = rX*cos(a)*(sqrt(a+1)), yy = rY*sin(a)*(sqrt(a+1))
			//let xx = rX*cos(a), yy = rY*sin(a)
            moveTo(xx,yy)
		}
	}
}

fn drawPoly() {

	let nPts = 100, N = 10, x0 = 0, y0 = 0, R = 2
		
	shape(label = "poly") {
		moveTo(x0 + R, y0)
		waitUsec(10000)
		startMeasure()
		for i in range(1, N+1) {
			let ang = M_PI*2*i / N
			let X = x0 + R*cos(ang), Y = y0 + R*sin(ang)
			lineTo(X, Y, nPts)
		}
	}
}
*/

fn drawRect() {

	let Nx = 10, Ny = 10, D = 20, 
	    sizeX = 40, sizeY = 40
	
	rect(-sizeX, -sizeY, sizeX, sizeY, nrows=100, nCols=100,interp=1, label="Xrect")	
}

fn scanCircuit() {
	
	shape(label="circuit") { // beginning of the scan box..
	// 1 encoder = 50 um
	// 1 mm = 366 encoders, 1 encoder = 1000/366 um
		let scale = 366
		let x0 = 0, y0 = 0, R = 30, maxPts = 1000, step = 2, delay = 25000
		
		for y in range(-R + step, R - step, step) { 
			let x = sqrt(R*R - y*y)
			moveTo(x0 - x, y0 + y)
			waitUsec(delay)
			startMeasure()
			// -x mm until x mm
			let num = 2*x // / 0.05
			//let num = x * maxPts / R
			lineTo(x0 + x, y0 + y, num)
			stopMeasure()
		}
	}
}


fn main(scanFreq = 10000,markerDelay=5000) {

	//ellipse(x0=0.0000, y0=0.0000, radX=15.0000, radY=5.0000, angle=45.0000, nTurns=1.0000, numPts=5000,waitAtBegin=10000, label="ellY")
	
   //for i in range(1){
        while(numIters = 1){
		   //setMarker(0)
		   //ellipse(x0=i, y0=0.0000, radX=15.0000, radY=5.0000, angle=45.0000, nTurns=1.0000, numPts=5000,waitAtBegin=10000, label="ellY")
           //line(x1=i*2, y1=-30, x2=30, y2=30, numPts=5000, waitAtBegin=5000, label="line2")
		   drawRect()
         //line(x1=-30, y1=-30, x2=30, y2=30, numPts=200, waitAtBegin=5000, label="line1")
        }
   //}
	
	//drawCircle()	
	
	/*dwd{
		let num = 16, L = 0, R = 5500, wofs = 100
		let wsz = (R - L - (num + 1)*wofs) / num
		for i in range(0,num) {
			let left1 = i * (wsz + wofs) + wofs
			add(left=left1, right=left1 + wsz, wndID=i)
		}
	}
	waitTrigger()*/
	
	//ellipse(x0=0.0000, y0=0.0000, radX=15.0000, radY=5.0000, angle=45.0000, nTurns=1.0000, numPts=5000,waitAtBegin=10000, label="ellY")

	//drawCircle()	

	// let scale = 366
	// for a in range(0,100,10) {
		// ellipse(x0=0, y0=0, radX=40, radY =20, angle=a, nTurns =3, numPts =30000, waitAtBegin =45000, label="ell")
	// }

}
