<?php

namespace App\Http\Controllers;

use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Validator;
use Illuminate\Http\Request;
use App\Models\Cart;
use App\Helpers\ResponseHelper;
use GuzzleHttp\Client;

class CartController extends Controller
{
    private $client;

    public function __construct()
    {
        $appEnv = env('APP_ENV', 'local');
        $baseUri = $appEnv === 'local' ? 'http://localhost:3000' : 'http://product-service:3000';
        $this->client = new Client(['base_uri' => $baseUri]);
    }

    private function getProduct($productId = null)
    {
        try {
            $url = $productId ? "/products/{$productId}" : '/products';
            $response = $this->client->get($url);
            $responseData = json_decode($response->getBody(), true);

            if ($response->getStatusCode() === 200 && isset($responseData['data'])) {
                return $responseData['data'];
            }

            return null;
        } catch (\Throwable $th) {
            Log::error('Error fetching product', [
                'message' => $th->getMessage(),
                'file' => $th->getFile(),
                'line' => $th->getLine(),
            ]);

            return null;
        }
    }

    public function index()
    {
        try {
            $cartItems = Cart::orderBy('created_at', 'desc')->get();
            return ResponseHelper::successResponse('Cart items fetched successfully', $cartItems);
        } catch (\Throwable $th) {
            Log::error('Error fetching cart items', [
                'message' => $th->getMessage(),
                'file' => $th->getFile(),
                'line' => $th->getLine(),
            ]);

            return ResponseHelper::errorResponse($th->getMessage());
        }
    }

    public function show($id)
    {
        try {
            $cartItem = Cart::find($id);
            if (!$cartItem) {
                return ResponseHelper::errorResponse('Cart item not found', 404);
            }

            return ResponseHelper::successResponse('Cart item fetched successfully', $cartItem);
        } catch (\Throwable $th) {
            Log::error('Error fetching cart item', [
                'message' => $th->getMessage(),
                'file' => $th->getFile(),
                'line' => $th->getLine(),
            ]);

            return ResponseHelper::errorResponse($th->getMessage());
        }
    }

    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'product_id' => 'required|integer',
            'quantity' => 'required|integer|min:1',
        ]);

        if ($validator->fails()) {
            return ResponseHelper::errorResponse('Validation failed', 422, $validator->errors());
        }

        $validated = $validator->validated();

        try {
            $product = $this->getProduct($validated['product_id']);
            if (!$product) {
                return ResponseHelper::errorResponse('Product not found', 404);
            }

            $cartItem = Cart::create([
                'product_id' => $validated['product_id'],
                'name' => $product['name'],
                'quantity' => $validated['quantity'],
                'price' => $product['price'] * $validated['quantity'],
            ]);

            return ResponseHelper::successResponse('Cart item created successfully', $cartItem);
        } catch (\Throwable $th) {
            Log::error('Error creating cart item', [
                'message' => $th->getMessage(),
                'file' => $th->getFile(),
                'line' => $th->getLine(),
            ]);

            return ResponseHelper::errorResponse($th->getMessage());
        }
    }

    public function update(Request $request, $id)
    {
        $validator = Validator::make($request->all(), [
            'quantity' => 'required|integer|min:1',
        ]);

        if ($validator->fails()) {
            return ResponseHelper::errorResponse('Validation failed', 422, $validator->errors());
        }

        $validated = $validator->validated();

        try {
            $cartItem = Cart::find($id);
            if (!$cartItem) {
                return ResponseHelper::errorResponse('Cart item not found', 404);
            }

            $product = $this->getProduct($cartItem->product_id);
            if (!$product || !isset($product['price'])) {
                return ResponseHelper::errorResponse('Product not found or price unavailable', 404);
            }

            $cartItem->update([
                'quantity' => $validated['quantity'],
                'price' => $product['price'] * $validated['quantity'],
            ]);

            return ResponseHelper::successResponse('Cart item updated successfully', $cartItem);
        } catch (\Throwable $th) {
            Log::error('Error updating cart item', [
                'message' => $th->getMessage(),
                'file' => $th->getFile(),
                'line' => $th->getLine(),
            ]);

            return ResponseHelper::errorResponse($th->getMessage());
        }
    }

    public function destroy($id)
    {
        try {
            $cartItem = Cart::find($id);
            if (!$cartItem) {
                return ResponseHelper::errorResponse('Cart item not found', 404);
            }

            $cartItem->delete();
            return ResponseHelper::successResponse('Cart item deleted successfully');
        } catch (\Throwable $th) {
            Log::error('Error deleting cart item', [
                'message' => $th->getMessage(),
                'file' => $th->getFile(),
                'line' => $th->getLine(),
            ]);

            return ResponseHelper::errorResponse($th->getMessage());
        }
    }
}
